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


def extract_transactions(text):
    lines = text.strip().split("\n")
    transactions = []
    current_date = None

    number_transactions = 0

    for line in lines:
        if number_transactions == 31:
            return transactions

        if full_name in line:
            return transactions

        if "Pagamento em" in line:
            i = lines.index(line)
            lines.pop(i+1)
            lines.pop(i+2)
            number_transactions = number_transactions + 1
            continue
        if "BRL" in line or "USD" in line:
            i = lines.index(line)
            lines.pop(i + 1)
            number_transactions = number_transactions + 1
            continue
        # Identify and update the current date
        if re.match(r"\d{2} [A-Z]{3}", line.strip()):
            current_date = line.strip()
        # Identify monetary amounts and capture the last non-empty line as description
        elif re.match(r"^\d+,\d{2}$", line.strip()):
            amount = line.strip()
            description = transactions.pop()[1] if transactions else ""
            transactions.append([current_date, description, checkAndConvertToNegativeIfIsRefund(amount, description).replace('.', ',')])
            number_transactions = number_transactions + 1
        # Capture descriptions
        elif line.strip() and current_date:
            transactions.append([current_date, line.strip(), ""])

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
        # Certifique-se de que 'monthOfInvoice' está definido
        if monthOfInvoice:
            month_name = monthOfInvoice.lower()
            csv_filename = f'{month_name}.csv'  # Use o valor da variável aqui

            # Use o modo 'a' para anexar após a primeira página
            mode = 'a' if os.path.exists(csv_filename) else 'w'

            with open(csv_filename, mode, newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                if page_number == 3:  # Escreva o cabeçalho apenas na primeira vez
                    writer.writerow(["Data", "Descrição", "Valor"])
                    writer.writerow(["", "Total", "=SOMA(C3:C)"])
                writer.writerows(transactions)
