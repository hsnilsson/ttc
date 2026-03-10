@echo off
echo Debug ZIP extraction...

python -c "
import zipfile
import os

try:
    with zipfile.ZipFile('vips-dev-w64-all-8.18.0.zip', 'r') as zip_ref:
        print('ZIP contents:')
        for name in zip_ref.namelist()[:10]:  # Show first 10 files
            print(f'  {name}')
        print(f'Total files: {len(zip_ref.namelist())}')
        
        # Extract to C:\
        zip_ref.extractall('C:\\')
        print('Extraction completed')
        
        # Check if vips directory exists
        if os.path.exists('C:\\vips'):
            print('C:\\vips directory created')
            if os.path.exists('C:\\vips\\bin\\vips.exe'):
                print('vips.exe found!')
            else:
                print('vips.exe not found')
                print('Contents of C:\\vips:')
                for item in os.listdir('C:\\vips'):
                    print(f'  {item}')
        else:
            print('C:\\vips directory not found')
            print('Contents of C:\\:')
            for item in os.listdir('C:\\'):
                if 'vips' in item.lower():
                    print(f'  {item}')
                    
except Exception as e:
    print(f'Error: {e}')
"

pause
