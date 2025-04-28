import requests
import boto3
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Get these from environment variables for flexibility and security
HOSTED_ZONE_ID = os.environ.get('HOSTED_ZONE_ID')
DNS_NAMES_STR = os.environ.get('DNS_NAMES')
DNS_NAMES = [name.strip() for name in DNS_NAMES_STR.split(',')] if DNS_NAMES_STR else []

# AWS Region (adjust if needed, boto3 might pick it up from env/config)
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# TTL for the DNS record (seconds)
RECORD_TTL = int(os.environ.get('RECORD_TTL', 300))

# --- Input Validation ---
if not HOSTED_ZONE_ID:
    print("Error: HOSTED_ZONE_ID environment variable is not set.")
    sys.exit(1)

if not DNS_NAMES:
    print("Error: DNS_NAMES environment variable is not set or is empty.")
    sys.exit(1)

# Ensure DNS names end with a dot as required by Route53
DNS_NAMES = [name + '.' if not name.endswith('.') else name for name in DNS_NAMES]

print(f"Configured DNS names to update: {DNS_NAMES}")

# --- Functions ---

def get_external_ip():
    """Fetches the current external IP address."""
    try:
        # Using checkip.amazonaws.com is a common and reliable method
        response = requests.get('https://checkip.amazonaws.com')
        response.raise_for_status() # Raise an exception for bad status codes
        ip_address = response.text.strip()
        print(f"Current external IP: {ip_address}")
        return ip_address
    except requests.RequestException as e:
        print(f"Error getting external IP: {e}")
        return None

def get_route53_current_ip(hosted_zone_id, dns_name):
    """Gets the current IP address from the Route53 A record."""
    try:
        client = boto3.client('route53', region_name=AWS_REGION)
        response = client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            StartRecordName=dns_name,
            StartRecordType='A',
            MaxItems='1'
        )

        for record_set in response['ResourceRecordSets']:
            if record_set['Name'] == dns_name and record_set['Type'] == 'A':
                current_ip = record_set['ResourceRecords'][0]['Value']
                print(f"Current Route53 IP for {dns_name}: {current_ip}")
                return current_ip

        print(f"No A record found for {dns_name} in zone {hosted_zone_id}.")
        return None # Record does not exist

    except Exception as e:
        print(f"Error getting Route53 record for {dns_name}: {e}")
        return None

def update_route53_record(hosted_zone_id, dns_name, new_ip, ttl):
    """Updates the Route53 A record with the new IP address."""
    try:
        client = boto3.client('route53', region_name=AWS_REGION)
        response = client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch={
                'Changes': [
                    {
                        'Action': 'UPSERT', # Use UPSERT to create if not exists, or update if exists
                        'ResourceRecordSet': {
                            'Name': dns_name,
                            'Type': 'A',
                            'TTL': ttl,
                            'ResourceRecords': [{'Value': new_ip}]
                        }
                    }
                ]
            }
        )
        print(f"Successfully initiated Route53 update for {dns_name} to {new_ip}. Change ID: {response['ChangeInfo']['Id']}")
        return True
    except Exception as e:
        print(f"Error updating Route53 record for {dns_name}: {e}")
        return False

# --- Main Logic ---

if __name__ == "__main__":
    print(f"[{time.ctime()}] Starting Route53 updater. Checking every {RECORD_TTL} seconds for DNS names: {DNS_NAMES}")

    while True: # Infinite loop to keep the script running
        try:
            current_external_ip = get_external_ip()
            if not current_external_ip:
                print(f"[{time.ctime()}] Skipping update cycle due to failure getting external IP.")
                # Continue loop, but don't try to update DNS
            else:
                # Loop through each configured DNS name
                for dns_name in DNS_NAMES:
                    current_route53_ip = get_route53_current_ip(HOSTED_ZONE_ID, dns_name)

                    if current_route53_ip == current_external_ip:
                        print(f"[{time.ctime()}] IP addresses match for {dns_name}. No DNS update needed.")
                    else:
                        print(f"[{time.ctime()}] IP mismatch for {dns_name}: External={current_external_ip}, Route53={current_route53_ip}")
                        print(f"[{time.ctime()}] Updating Route53 record {dns_name} to {current_external_ip}...")
                        update_route53_record(HOSTED_ZONE_ID, dns_name, current_external_ip, RECORD_TTL)

        except Exception as e:
            # Catch any unexpected errors in the loop to prevent script from crashing
            print(f"[{time.ctime()}] An unexpected error occurred in the loop: {e}")

        print(f"[{time.ctime()}] Finished check cycle. Sleeping for {RECORD_TTL} seconds...")
        time.sleep(RECORD_TTL) # Wait before the next check