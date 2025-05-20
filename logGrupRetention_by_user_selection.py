import boto3
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpyxl import Workbook
from openpyxl.styles import Alignment
from datetime import datetime
import time
from botocore.exceptions import EndpointConnectionError


def convert_bytes(size_in_bytes):
    """
    Convert bytes into a human-readable format (Bytes, KB, MB, GB, TB, PB).
    """
    if size_in_bytes == 0:
        return "0 Bytes"

    size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB")
    i = int((len(str(size_in_bytes)) - 1) // 3)
    p = 1024 ** i
    s = round(size_in_bytes / p, 2)
    return f"{s} {size_name[i]}"


def change_retention_period(region, log_group_name, account_id, user_name, new_retention_days):
    client = boto3.client('logs', region_name=region,
                          config=boto3.session.Config(retries={'max_attempts': 10, 'mode': 'standard'}))
    try:
        response = client.describe_log_groups(logGroupNamePrefix=log_group_name)

        if not response['logGroups']:
            return {
                'Account ID': account_id,
                'Region': region,
                'Log Group Name': log_group_name,
                'User Name': user_name,
                'Status': "LogGroup doesn't exist"
            }

        log_group = response['logGroups'][0]
        old_retention = log_group.get('retentionInDays', 'Never')
        stored_bytes = log_group['storedBytes']

        if new_retention_days == 0:
            # Remove the retention policy for "never expire"
            client.delete_retention_policy(logGroupName=log_group_name)
            new_retention_days_text = 'Never'
        else:
            # Change the retention period with exponential backoff
            max_attempts = 5
            attempt = 0
            while attempt < max_attempts:
                try:
                    client.put_retention_policy(logGroupName=log_group_name, retentionInDays=new_retention_days)
                    break
                except (client.exceptions.ThrottlingException, EndpointConnectionError) as e:
                    attempt += 1
                    wait_time = 2 ** attempt
                    print(f"Exception encountered ({str(e)}). Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
            else:
                return {
                    'Account ID': account_id,
                    'Region': region,
                    'LogGroup Name': log_group['logGroupName'],
                    'User Name': user_name,
                    'Status': 'Failed due to throttling or connection issues'
                }
            new_retention_days_text = new_retention_days

        return {
            'Account ID': account_id,
            'Region': region,
            'LogGroup Name': log_group['logGroupName'],
            'ARN': log_group['arn'],
            'Log Class': log_group.get('kmsKeyId', 'Standard'),
            'Old Retention': old_retention,
            'New Retention': new_retention_days_text,
            'Stored Bytes': convert_bytes(stored_bytes),
            'User Name': user_name,
            'Status': 'Updated successfully'
        }
    except Exception as e:
        return {
            'Account ID': account_id,
            'Region': region,
            'LogGroup Name': log_group_name,
            'User Name': user_name,
            'Status': f'Error: {str(e)}'
        }


def generate_filename_with_datetime(base_filename='log_groups_retention_change'):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{base_filename}_{current_time}.xlsx"


def save_to_excel(data, filename):
    df = pd.DataFrame(data)

    # Create a workbook and add a worksheet
    workbook = Workbook()
    sheet = workbook.active

    # Write the header
    sheet.append(df.columns.tolist())

    # Write the data
    for row in df.itertuples(index=False):
        sheet.append(row)

    # Apply left alignment to all cells
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(horizontal='left')

    # Save the workbook
    workbook.save(filename)
    print(f'Log groups inventory saved to {filename}')


def main(regions, log_group_names_file):
    sts_client = boto3.client('sts')
    identity = sts_client.get_caller_identity()
    account_id = identity['Account']
    user_name = identity['Arn'].split('/')[-1]  # Extract the role name or user name

    with open(log_group_names_file, 'r') as file:
        log_group_names = [line.strip() for line in file if line.strip()]

    # Ask the user for the new retention period
    valid_retention_periods = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557,
                               2922, 3288, 3653]
    print("Choose the new retention period from the following options (in days), or enter 'Never' for no expiration:")
    print(valid_retention_periods, "or 'Never'")

    while True:
        user_input = input("Enter your choice: ").strip()
        if user_input.lower() == 'never':
            new_retention_days = 0
            break
        try:
            new_retention_days = int(user_input)
            if new_retention_days in valid_retention_periods:
                break
            else:
                print("Invalid choice. Please enter a valid retention period from the list.")
        except ValueError:
            print("Invalid input. Please enter a number or 'Never'.")

    updated_log_groups = []

    # Use ThreadPoolExecutor for concurrency
    with ThreadPoolExecutor(max_workers=len(regions) * len(log_group_names)) as executor:
        future_to_log_group = {
            executor.submit(change_retention_period, region, log_group_name, account_id, user_name,
                            new_retention_days): (region, log_group_name)
            for region in regions
            for log_group_name in log_group_names
        }

        for future in as_completed(future_to_log_group):
            region, log_group_name = future_to_log_group[future]
            try:
                details = future.result()
                updated_log_groups.append(details)
                print(f"Processed log group '{log_group_name}' in region '{region}': {details['Status']}")
            except Exception as e:
                print(f'Error processing log group {log_group_name} in region {region}: {str(e)}')

    if updated_log_groups:
        filename = generate_filename_with_datetime()
        save_to_excel(updated_log_groups, filename)
    else:
        print('No log groups were updated.')


if __name__ == '__main__':
    # Specify the AWS regions you want to query
    regions_to_query = ['us-east-1']

    # Specify the text file containing log group names
    log_group_names_file = 'log_group_names.txt'

    # Run the main function
    main(regions_to_query, log_group_names_file)