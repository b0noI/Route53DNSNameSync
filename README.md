# **AWS Route53 Dynamic DNS Updater**

This project provides a simple Python application, containerized with Docker, to automatically update an AWS Route53 A record with your current external IP address. This is useful for scenarios like having a dynamic IP address from your ISP but needing a consistent domain name pointing to your location (e.g., for accessing a home server or VPN endpoint).
The application runs periodically, checks your current external IP, compares it to the IP currently configured in Route53 for a specified DNS name, and updates the Route53 record if they don't match.

## **Features**

* Fetches current external IP address.
* Checks existing A record in AWS Route53.
* Updates the Route53 A record if the IP address has changed.
* Runs as a background daemon using Docker.
* Configuration via environment variables (preferably loaded from a .env file).
* Includes a helper script (run\_updater.sh) to manage the container lifecycle (stop, remove, run).

## **Prerequisites**

Before you begin, ensure you have the following:

1. **An AWS Account:** You need an active AWS account.
2. **AWS Route53 Hosted Zone:** A public hosted zone in Route53 for the domain you want to update (e.g., kovalevskyi.com).
3. **AWS Credentials:** An IAM user with permissions to list and change resource record sets in your specific Route53 hosted zone. **Using root account credentials is strongly discouraged.**
4. **Docker:** Docker installed and running on the machine where you will run the updater.

## **AWS Setup**

### **1\. Create an IAM User (Recommended)**

1. Go to the AWS IAM Console.
2. Navigate to **Users** and click **Add users**.
3. Give the user a descriptive name (e.g., route53-updater).
4. Select **Access key \- Programmatic access** as the AWS access type.
5. Click **Next: Permissions**.
6. Attach an existing policy directly or create a new policy. For least privilege, create a custom policy.

### **2\. Create IAM Policy**

Create a policy that grants only the necessary permissions for Route53 updates. Replace YOUR\_HOSTED\_ZONE\_ID with your actual Route53 Hosted Zone ID.
{
    "Version": "2012-10-17",
    "Statement": \[
        {
            "Effect": "Allow",
            "Action": \[
                "route53:ListResourceRecordSets",
                "route53:ChangeResourceRecordSets"
            \],
            "Resource": "arn:aws:route53:::hostedzone/YOUR\_HOSTED\_ZONE\_ID"
        }
    \]
}

Attach this policy to the IAM user you created.

### **3\. Obtain Access Keys**

After creating the IAM user and attaching the policy, you will be presented with the **Access key ID** and **Secret access key**. **Copy these immediately and store them securely.** You will not be able to retrieve the Secret Access Key again after this step.

### **4\. Get Hosted Zone ID**

Go to the AWS Route53 Console, navigate to **Hosted zones**, and click on your domain's hosted zone. The **Hosted Zone ID** will be displayed on the details page (starts with Z). Copy this ID.

## **Project Structure**

The project consists of the following files:
.
├── Dockerfile
├── .env.example
├── requirements.txt
├── run\_updater.sh
└── update\_dns.py

* **Dockerfile**: Defines the Docker image for the application.
* **.env.example**: An example file showing the required and optional environment variables. Copy this to .env and fill in your details.
* **requirements.txt**: Lists the Python dependencies (boto3, requests).
* **run\_updater.sh**: A Bash script to build the image, and then stop, remove, and start the container as a daemon.
* **update\_dns.py**: The main Python script that performs the IP check and Route53 update.

## **Setup and Running**

1. **Clone the repository:**
   git clone \<repository\_url\>
   cd \<repository\_directory\>

2. Create .env file:
   Copy the example environment file:
   cp .env.example .env

   Edit the .env file and fill in your AWS credentials, Hosted Zone ID, and the DNS name you want to update.
   \# .env file

   \# Required: Your AWS Route53 Hosted Zone ID
   HOSTED\_ZONE\_ID=YOUR\_HOSTED\_ZONE\_ID

   \# Required: Your AWS Access Key ID
   AWS\_ACCESS\_KEY\_ID=YOUR\_AWS\_ACCESS\_KEY\_ID

   \# Required: Your AWS Secret Access Key
   AWS\_SECRET\_ACCESS\_KEY=YOUR\_AWS\_SECRET\_ACCESS\_KEY

   \# Optional: The specific DNS name to update (defaults to vpn.kovalevskyi.com)
   \# DNS\_NAME=vpn.kovalevskyi.com

   \# Optional: AWS Region (defaults to us-east-1 in the script)
   \# AWS\_REGION=us-west-2

   \# Optional: TTL for the record in seconds (defaults to 300\)
   \# RECORD\_TTL=60

   \# Optional: Interval between checks in seconds (defaults to 300 \= 5 minutes)
   \# CHECK\_INTERVAL\_SECONDS=60

   **Security Note:** Storing credentials in a .env file is suitable for testing or development on a secured machine. For production environments, consider more secure methods like IAM roles if running on AWS infrastructure (EC2, ECS, EKS) or using AWS Secrets Manager.
3. **Make the run script executable:**
   chmod \+x run\_updater.sh

4. Run the updater:
   Execute the helper script. This will build the Docker image (if not already built), stop and remove any existing container with the same name, and start a new container in detached (daemon) mode.
   ./run\_updater.sh

## **Managing the Container**

* **Check container status:**
  docker ps \-f name=route53-updater-daemon

* **View logs:**
  docker logs \-f route53-updater-daemon

* **Stop the container:**
  docker stop route53-updater-daemon

* **Start the container (if stopped):**
  docker start route53-updater-daemon

* **Remove the container (must be stopped first):**
  docker rm route53-updater-daemon

* **Rebuild and restart:** If you make changes to the code or Dockerfile, run ./run\_updater.sh again.

## **Security Considerations**

* **AWS Credentials:** As mentioned, avoid using root account credentials. Use an IAM user with minimal necessary permissions limited to the specific Hosted Zone.
* **.env file:** Secure your .env file. Do not commit it to public repositories. If running on a server, ensure the file permissions are restrictive.
* **Network Access:** The container needs outbound internet access to fetch the external IP and communicate with the AWS Route53 API endpoints.

## **Customization**

* **DNS Name:** Change the DNS\_NAME variable in the .env file to update a different A record.
* **Check Interval:** Adjust CHECK\_INTERVAL\_SECONDS in the .env file to change how often the script checks the IP. Be mindful of making API calls too frequently.
* **TTL:** Modify RECORD\_TTL in the .env file to set the Time-To-Live for the DNS record.

This README should provide a good starting point for anyone wanting to use or contribute to your Route53 Dynamic DNS Updater project.