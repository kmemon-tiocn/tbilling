from main.services import AWSAccountManager
import datetime

# if __name__ == "__main__":
#     # print('.'*15, env('AWS_ACCESS_KEY_ID'), env('AWS_SECRET_ACCESS_KEY'))
#     # Initialize the billing manager
#     billing_manager = AWSAccountManager(env('AWS_ACCESS_KEY_ID'), env('AWS_SECRET_ACCESS_KEY'))
    
#     # Set date range for report
#     start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
#     end_date = datetime.now().strftime('%Y-%m-%d')
    
#     hello = billing_manager.get_linked_accounts()
#     print('-'*25, hello)
#     # # Generate and export billing report
#     report_df = billing_manager.generate_billing_report(start_date)
#     print(report_df)
#     # billing_manager.export_report_to_csv(report_df, 'aws_billing_report.csv')
    
#     # Check for cost alerts
#     alerts = billing_manager.get_account_cost_alerts(threshold=1000.0)
#     for alert in alerts:
#         print(f"Alert: Account {alert['account_id']} exceeded threshold of ${alert['threshold']}")


def get_latest_cost_explorer_data(aws_access_key_id, aws_secrect_access_key):
    billing_manager = AWSAccountManager(aws_access_key_id, aws_secrect_access_key)
    start_date = datetime.now().strftime('%Y-%m-%d')

    report_df = billing_manager.generate_billing_report(start_date)
    return report_df