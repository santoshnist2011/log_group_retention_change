```markdown
# AWS CloudWatch Log Group Retention Manager

This Python script allows users to change the retention period of AWS CloudWatch Log Groups across multiple regions. Users can select from a predefined list of retention periods or choose to set the log groups to "Never Expire."

## Features

- Update the retention period for multiple AWS CloudWatch Log Groups.
- Supports multiple AWS regions.
- Allows retention period selection from a predefined list or "Never Expire."
- Concurrent processing of log groups for efficient execution.
- Generates an Excel report of the status of each log group update.

## Prerequisites

- Python 3.x
- AWS SDK for Python (Boto3)
- Pandas
- OpenPyXL
- AWS credentials configured to allow access to CloudWatch Logs and STS.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Install the required Python packages**:
   ```bash
   pip install boto3 pandas openpyxl
   ```

## Usage

1. **Configure AWS Credentials**:
   Ensure your AWS credentials are configured in your environment. You can use the AWS CLI to configure credentials:
   ```bash
   aws configure
   ```

2. **Prepare Log Group Names File**:
   Create a text file named `log_group_names.txt` containing the names of the log groups you want to update. Each log group name should be on a separate line.

3. **Run the Script**:
   Execute the script using Python:
   ```bash
   python log_group_retention_manager.py
   ```

4. **Select Retention Period**:
   The script will prompt you to choose a retention period from a list or enter "Never" for no expiration.

5. **Review Results**:
   An Excel file will be generated with the status of each log group's retention update.

## Example

Here's an example of what the log group names file might look like:

```
/aws/lambda/my-first-lambda
/aws/lambda/my-second-lambda
/aws/ec2/my-instance-log
```

Upon running the script, you will be prompted to enter a retention period from the list `[1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653]` or "Never."

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or feedback, please contact [your-email@example.com](mailto:your-email@example.com).
```

Once you've saved the file, you can upload it to your GitHub repository where your Python script resides. Make sure to replace placeholders with actual values specific to your project.
