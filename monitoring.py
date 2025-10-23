import os
import zipfile
from datetime import datetime
import argparse

def create_backup(source_paths, backup_dir):
    
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
        
    timestamp= datetime.now().strftime('%d-%m-%Y_%H-%M-%S')   
    zipfile_name = f"backup_{timestamp}.zip"
    zip_path=  os.path.join(backup_dir , zipfile_name)
    
    try:
        with zipfile.ZipFile(zip_path , 'w' , zipfile.ZIP_DEFLATED) as zipf:
            for source in source_paths :
                if os.path.isfile(source):
                    zipf.write(source , os.path.basename(source))
                elif os.path.isdir(source):
                    for root, dirs , files in os.walk(source):
                        for file in files :
                            file_path= os.path.join(root, file)
                            
                            arcname= os.path.relpath(file_path , os.path.dirname(source))
                            zipf.write(file_path,arcname)    
                else:
                    print(f"Warning: Skipping invalid path {source}")    
        print(f"Backup created successfully: {zip_path}")
    except Exception as e:
        print(f"Error during backup: {e}")
        
if __name__ == "__main__":
    parser= argparse.ArgumentParser(description="backup to ZIP")
    parser.add_argument('--sources', nargs='+', required=True , help="paths to files to backup")
    parser.add_argument('--backup_dir', default='./backups', help="Directory to store backups (default: ./backups)")
    args = parser.parse_args()
    create_backup(args.sources, args.backup_dir)