import csv
import sys

# input number you want to search
number = input('Enter number to find\n')

# read csv, and split on "," the line
csv_file = csv.reader(open('CARS_2.csv', "r"), delimiter=",")


# loop through the csv list
for row in csv_file:
    # if current rows 2nd value is equal to input, print that row
    if(row[12] == 'Mileage Km/L'):
        continue
    else:
        num1 = float(number)
        num2 = float(row[12])
        if abs(num1-num2) <= 1:
            print(row[1])


    #print(type(num1), type(num2))
    # if abs((number-'0')-(row[12]-'0')) <= 1:
    #     print(row[1])
