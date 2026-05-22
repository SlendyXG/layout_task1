import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import collections
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
import pandas


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Генератор сайта магазина напитков'
    )
    parser.add_argument(
        '--data_file',
        type=str,
        default='wine3.xlsx',
        help='Путь к Excel-файлу с данными (по умолчанию: wine3.xlsx)'
    )
    parser.add_argument(
        '--template_file',
        type=str,
        default='template.html',
        help='Путь к HTML-шаблону (по умолчанию: template.html)'
    )
    parser.add_argument(
        '--output_file',
        type=str,
        default='index.html',
        help='Путь для сохранения результата (по умолчанию: index.html)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Порт для веб-сервера (по умолчанию: 8080)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Хост для веб-сервера (по умолчанию: 0.0.0.0)'
    )
    parser.add_argument(
        '--no-server',
        action='store_true',
        help='Не запускать веб-сервер'
    )

    return parser.parse_args()


def get_years_data():
    current_year = datetime.now().year
    years_working = current_year - 1920
    return years_working


def get_correct_word(years_working):
    last_digit = years_working % 10
    last_two_digits = years_working % 100

    if 11 <= last_two_digits <= 14:
        word = "лет"
    else:
        if last_digit == 1:
            word = "год"
        elif 2 <= last_digit <= 4:
            word = "года"
        else:
            word = "лет"

    return word


def find_cheapest_product(excel_data):
    min_price = float('inf')
    cheapest_product_name = None

    for _, row in excel_data.iterrows():
        price = row['Цена']
        if price < min_price:
            min_price = price
            cheapest_product_name = row['Название']

    return cheapest_product_name


def load_drinks_from_excel(excel_data, cheapest_product_name):
    drinks = collections.defaultdict(list)

    for _, row in excel_data.iterrows():
        category = row['Категория']
        sort_value = row['Сорт'] if pandas.notna(row['Сорт']) else ''
        sale_value = row['Акция'] if pandas.notna(row['Акция']) else ''

        drink_info = {
            'название': row['Название'],
            'сорт': sort_value,
            'цена': row['Цена'],
            'картинка': row['Картинка'],
            'акция': sale_value,
            'самый_дешевый': row['Название'] == cheapest_product_name
        }

        drinks[category].append(drink_info)

    return drinks


def main():
    args = parse_arguments()

    data_path = Path(args.data_file)
    template_path = Path(args.template_file)

    if not data_path.exists():
        print(f"Ошибка: Файл данных '{args.data_file}' не найден")
        return

    if not template_path.exists():
        print(f"Ошибка: Файл шаблона '{args.template_file}' не найден")
        return

    print(f"Использую файл данных: {args.data_file}")
    print(f"Использую шаблон: {args.template_file}")

    excel_data = pandas.read_excel(args.data_file)
    cheapest_product_name = find_cheapest_product(excel_data)
    drinks = load_drinks_from_excel(excel_data, cheapest_product_name)

    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    years_working = get_years_data()
    word = get_correct_word(years_working)

    template = env.get_template(args.template_file)
    rendered_page = template.render(
        years_working=years_working,
        word=word,
        drinks=drinks,
    )

    with open(args.output_file, 'w', encoding="utf8") as file:
        file.write(rendered_page)

    print(f"Сайт сохранен в: {args.output_file}")

    if not args.no_server:
        print(f"Запускаю сервер на {args.host}:{args.port}")
        server = HTTPServer((args.host, args.port), SimpleHTTPRequestHandler)
        server.serve_forever()
    else:
        print("Сервер не запущен (флаг --no-server)")

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    server.serve_forever()


if __name__ == '__main__':
    main()