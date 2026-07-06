import argparse
import re
from pathlib import Path


def clean_roster(text):
    students = []

    for line in text.splitlines():
        parts = line.split('\t')

        if len(parts) > 3 and parts[-1].strip() == 'Student':
            namepart = parts[1].strip()
            namepart = re.sub(r'\s*\([^)]*\)', '', namepart)

            name_parts = namepart.split(',')
            if len(name_parts) >= 2:
                surname = name_parts[0].strip()
                first_name_part = name_parts[1].strip()
                first_name = first_name_part.split()[0] if first_name_part else ''
                cleaned_name = f'{surname}, {first_name}'
            else:
                cleaned_name = namepart

            students.append(cleaned_name)

    return students


def process_file(input_path, output_path):
    text = Path(input_path).read_text(encoding='utf-8')
    students = clean_roster(text)
    Path(output_path).write_text('\n'.join(students) + '\n', encoding='utf-8')
    print(f'Successfully processed {len(students)} students and saved to {output_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Clean a raw roster export into surname, first-name format.'
    )
    parser.add_argument(
        'input',
        nargs='?',
        default='student_roster_raw.txt',
        help='Path to the raw roster export text file.',
    )
    parser.add_argument(
        '-o',
        '--output',
        default='cleaned_student_roster.txt',
        help='Path to the cleaned output file.',
    )

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(
            f'Input file not found: {input_path}. '
            'This utility is optional and only runs when you provide a local roster export.'
        )
        return 1

    process_file(input_path, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
