import zipfile
import os
import sys

def extract_vips():
    zip_file = 'vips-dev-w64-all-8.18.0.zip'
    
    try:
        print(f'Extracting {zip_file}...')
        
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            # List contents
            print('ZIP contents:')
            for name in zip_ref.namelist()[:10]:
                print(f'  {name}')
            print(f'Total files: {len(zip_ref.namelist())}')
            
            # Extract to C:\
            zip_ref.extractall('C:\\')
            print('Extraction completed')
            
            # Check if VIPS was installed
            if os.path.exists('C:\\vips'):
                print('C:\\vips directory created')
                if os.path.exists('C:\\vips\\bin\\vips.exe'):
                    print('vips.exe found!')
                    return True
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
        return False
    
    return False

if __name__ == '__main__':
    success = extract_vips()
    sys.exit(0 if success else 1)
