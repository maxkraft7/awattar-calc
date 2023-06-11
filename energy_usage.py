# conversation:
# https://app.textcortex.com/user/dashboard/chat?conversation=8fed5242-48ce-4045-baaf-08d5619d6a48

import argparse
import pandas as pd
from datetime import datetime
from awattar.client import AwattarClient
from netznoe_smartmeter_portal_api import NetzNoeSmartmeterPortalApi

# define the command-line arguments
parser = argparse.ArgumentParser(description='Calculate the cost of energy usage over a given time period.')
parser.add_argument('username', type=str, help='your smart meter portal username')
parser.add_argument('password', type=str, help='your smart meter portal password')
parser.add_argument('smartMeterId', type=str, help='the ID of your smart meter')
parser.add_argument('startDate', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help='the start date of the time period (format: YYYY-MM-DD)')
parser.add_argument('endDate', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), help='the end date of the time period (format: YYYY-MM-DD)')

# parse the command-line arguments
args = parser.parse_args()


# retrieve the hourly energy prices from awattar
awattar = AwattarClient('AT')
prices = awattar.request(args.startDate, args.endDate)

# retrieve the hourly energy usage from the smart meter API
api = NetzNoeSmartmeterPortalApi(username=args.username, password=args.password)
data = api.get_week(args.smartMeterId, args.startDate, args.endDate)

# create a pandas DataFrame to store the data
df = pd.DataFrame({'Timestamp': pd.date_range(start=args.startDate, end=args.endDate, freq='H'),
                   'Energy Usage (kWh)': data,
                   'Hourly Price (€/kWh)': prices})

# calculate the total cost of energy usage
df['Total Cost (€)'] = df['Energy Usage (kWh)'] * df['Hourly Price (€/kWh)']
total_cost = df['Total Cost (€)'].sum()

# export the data to an Excel file
filename = 'energy_usage.xlsx'
df.to_excel(filename, index=False)

print(f'Total cost of energy usage: {total_cost:.2f} €')


