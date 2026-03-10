@echo off
echo Debug ZIP extraction...

python -c ^
"import zipfile; ^
import os; ^
try: ^
    with zipfile.ZipFile('vips-dev-w64-all-8.18.0.zip', 'r') as zip_ref: ^
        print('ZIP contents:'); ^
        for name in zip_ref.namelist()[:10]: ^
            print(f'  {name}'); ^
        print(f'Total files: {len(zip_ref.namelist())}'); ^
        zip_ref.extractall('C:\\'); ^
        print('Extraction completed'); ^
        if os.path.exists('C:\\vips'): ^
            print('C:\\vips directory created'); ^
            if os.path.exists('C:\\vips\\bin\\vips.exe'): ^
                print('vips.exe found!'); ^
            else: ^
                print('vips.exe not found'); ^
        else: ^
            print('C:\\vips directory not found'); ^
except Exception as e: ^
    print(f'Error: {e}')"

pause
