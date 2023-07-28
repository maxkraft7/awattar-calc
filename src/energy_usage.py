import argparse
import pandas as pd
from datetime import datetime
from awattar.client import AwattarClient
from netznoe_smartmeter_portal_api import NetzNoeSmartmeterPortalApi
import datetime

# define the command-line arguments
parser = argparse.ArgumentParser(description='Calculate the cost of energy usage over a given time period.')
parser.add_argument('username', type=str, help='your smart meter portal username')
parser.add_argument('password', type=str, help='your smart meter portal password')
parser.add_argument('smartMeterId', type=str, help='the ID of your smart meter')
parser.add_argument('startDate', type=str, help='the start date of the time period (format: YYYY-MM-DD)')
parser.add_argument('endDate', type=str, help='the end date of the time period (format: YYYY-MM-DD)')

# parse the command-line arguments
args = parser.parse_args()


# retrieve the hourly energy prices from awattar
awattar = AwattarClient('AT')

# parse date string from the command-line arguments to date objects
args.startDate = datetime.datetime.strptime(args.startDate, '%Y-%m-%d')
args.endDate = datetime.datetime.strptime(args.endDate, '%Y-%m-%d')


hourlyPrices = awattar.request(args.startDate, args.endDate)

day_prices = {}

for hour in hourlyPrices:
    date = hour.start_datetime.strftime("%Y-%m-%d")
    if date not in day_prices:
        day_prices[date] = []
    day_prices[date].append(hour.price_per_kWh)



for date in day_prices:
    day_prices[date] = sum(day_prices[date]) / len(day_prices[date])

day_prices_parsed = {}

for date in day_prices:
    # parse datestring to date object
    date_parsed = datetime.datetime.strptime(date, '%Y-%m-%d')
    # add the date and the average price to the dictionary
    day_prices_parsed[date_parsed] = day_prices[date]


# retrieve the hourly energy usage from the smart meter API
api = NetzNoeSmartmeterPortalApi(username=args.username, password=args.password)
api.do_login()

dailyUsageData = api.get_week(args.smartMeterId, args.startDate, args.endDate)
consumption_metered = dailyUsageData.consumption_metered

consumption_metered_parsed = {}
# parse the datestring to a date object
for date in consumption_metered:
    date_parsed = datetime.datetime.strptime(date.to_date_string(), '%Y-%m-%d')
    # add the date and the average price to the dictionary
    consumption_metered_parsed[date_parsed] = consumption_metered[date]

# only use the dates that are keys in day_prices_parsed and consumption_metered
trimmed_consumption = {}

# only use the dates that are keys in consumption_metered and day_prices_parsed
trimmed_prices = {}

for date in consumption_metered_parsed.keys():
    if date in day_prices_parsed.keys():
        trimmed_consumption[date] = consumption_metered_parsed[date]

for date in day_prices_parsed.keys():
    if date in consumption_metered_parsed.keys():
        trimmed_prices[date] = day_prices_parsed[date]

# 
excel_non_readable = list(trimmed_consumption.keys())

# convert the date objects to strings
excel_readable = [date.strftime("%Y-%m-%d") for date in excel_non_readable]
     

# create a pandas DataFrame to store the data
df = pd.DataFrame({'Timestamp': excel_readable,
                   'Energy Usage (kWh)': trimmed_consumption.values(),
                   'Hourly Price (€/kWh)': trimmed_prices.values()})

# calculate the total cost of energy usage
df['Total Cost (€)'] = df['Energy Usage (kWh)'] * df['Hourly Price (€/kWh)']
total_cost = df['Total Cost (€)'].sum()

# append the total cost to the DataFrame as excel formula (to be calculated in Excel)
df = df._append({'Timestamp': 'Total Cost (€)',
                'Energy Usage (kWh)': '',
                'Hourly Price (€/kWh)': '',
                'Total Cost (€)': f'=SUM(D2:D{len(df)+1})'},
                ignore_index=True)


# export the data to an Excel file
filename = 'energy_usage.xlsx'
df.to_excel(filename, index=False)

print(f'Total cost of energy usage: {total_cost:.2f} €')


