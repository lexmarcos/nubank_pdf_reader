import PyPDF2
import re
import os
import csv

full_name = "MARCOSUEL VIEIRA DE ARRUDA FILHO"
def get_month_of_invoice(period_of_the_read):
    month_map = {
        'JAN': 'FEV', 'FEV': 'MAR', 'MAR': 'ABR',
        'ABR': 'MAI', 'MAI': 'JUN', 'JUN': 'JUL',
        'JUL': 'AGO', 'AGO': 'SET', 'SET': 'OUT',
        'OUT': 'NOV', 'NOV': 'DEZ', 'DEZ': 'JAN'
    }

    last_month_of_the_read = period_of_the_read.strip().split(' ')[-1]
    return month_map[last_month_of_the_read]

def cleanTheFirstLineOfTextToGetTheMonth(text):
    lines = text.split('\n')
    if len(lines) >= 2:
        return lines[1]
    return None

def checkAndConvertToNegativeIfIsRefund(amount, description):
    if 'Estorno' in description or 'Desconto' in description:
        return '-' + amount
    return amount

def handle_payment_line(lines, i, number_transactions):
    lines.pop(i + 1)
    lines.pop(i + 2)
    return number_transactions + 1

def handle_currency_line(lines, i, number_transactions):
    lines.pop(i + 1)
    return number_transactions + 1

def update_current_date(line):
    return line.strip()

def handle_amount_line(line, transactions, current_date):
    amount = line.strip()
    description = transactions.pop()[1] if transactions else ""
    return [[current_date, description, checkAndConvertToNegativeIfIsRefund(amount, description).replace('.', ',')]]

def handle_description_line(line, transactions, current_date):
    return [[current_date, line.strip(), ""]]

def extract_transactions(text):
    lines = text.strip().split("\n")
    transactions = []
    current_date = None
    number_transactions = 0
    MAX_NUMBER_TRANSACTIONS_PER_PDF_PAGE = 31

    is_date = re.match(r"\d{2} [A-Z]{3}", line.strip())
    is_money_value = re.match(r"^\d+,\d{2}$", line.strip())
    is_description_of_conversion = "BRL" in line or "USD" in line
    is_last_payment_line = "Pagamento em" in line

    for i, line in enumerate(lines):
        if number_transactions >= MAX_NUMBER_TRANSACTIONS_PER_PDF_PAGE or full_name in line:
            break

        if is_last_payment_line:
            number_transactions = handle_payment_line(lines, i, number_transactions)

        elif is_description_of_conversion:
            number_transactions = handle_currency_line(lines, i, number_transactions)

        elif is_date:
            current_date = update_current_date(line)

        elif is_money_value:
            transactions += handle_amount_line(line, transactions, current_date)
            number_transactions += 1

        elif line.strip() and current_date:
            transactions += handle_description_line(line, transactions, current_date)

    return transactions


with open(r'pdfs\Nubank_2024-02-01.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    num_pages = len(reader.pages)

    for page_number in range(3, num_pages):
        page = reader.pages[page_number]

        text = page.extract_text()

        if 'TRANSAÇÕES' in text:
            monthOfReadOfTheInvoice = cleanTheFirstLineOfTextToGetTheMonth(text)
            if monthOfReadOfTheInvoice is not None:
                monthOfInvoice = get_month_of_invoice(monthOfReadOfTheInvoice)

        transactions = extract_transactions(text)
        if monthOfInvoice:
            month_name = monthOfInvoice.lower()
            csv_filename = f'{month_name}.csv'

            mode = 'a' if os.path.exists(csv_filename) else 'w'

            with open(csv_filename, mode, newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                if page_number == 3:
                    writer.writerow(["Data", "Descrição", "Valor"])
                    writer.writerow(["", "Total", "=SOMA(C3:C)"])
                writer.writerows(transactions)
