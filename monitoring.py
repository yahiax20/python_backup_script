import os
import zipfile
from datetime import datetime
import argparse
import logging 
import yagmail
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler("backup.log", maxBytes=1000000, backupCount=5)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("backup.log"),
        logging.StreamHandler(),  # Keeps terminal output
        handler
    ]
)
logz = logging.getLogger(__name__)


def get_file_size_mb(file_path):
    if not os.path.exists(file_path):
        return 0 
    size_byte= os.path.getsize(file_path)
    return size_byte / (1024 * 1024)


def send_email(subject, body, to_email, from_email, password=None,attachment=None, oauth_file=None):

    try:
        if oauth_file:
            yag = yagmail.SMTP(from_email, oauth2_file=oauth_file)
        else:
            yag = yagmail.SMTP(from_email, password)    
    
        yag.send(
            to= to_email,
            subject=subject,
            contents=body,
            attachments=attachment if attachment else []
        )        
        logz.info(f"Email sent to {to_email} {'attachments ' if attachment else ''}")
    except Exception as e :
        logz.error(f"email failed : {e}")
        raise
        
        
        
def create_backup(source_paths, backup_dir, email_config=None , max_zip_size_mb=20 , attach_zip=True):
    
    logz.info(f"Backup started from dest: {source_paths} , to {backup_dir}")
    
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        logz.info(f"created directory for backup in {backup_dir}")
        
        
    timestamp= datetime.now().strftime('%d-%m-%Y_%H-%M-%S')   
    zipfile_name = f"backup_{timestamp}.zip"
    zip_path=  os.path.join(backup_dir , zipfile_name)
    
    try:
        
        with zipfile.ZipFile(zip_path , 'w' , zipfile.ZIP_DEFLATED) as zipf:
            for source in source_paths:
                source = os.path.expanduser(source)
                if not os.path.exists(source):
                    logz.warning(f"skipping this file missing {source}")
                    continue
                
                if os.path.isfile(source):
                    zipf.write(source, os.path.basename(source))
                    logz.info(f"Added file : {source}")
                else:
                    for root,  _, files in os.walk(source):
                        for file in files:
                            file_path= os.path.join(root, file)
                            arcname= os.path.relpath(file_path, os.path.dirname(source) )
                            zipf.write(file_path, arcname)
                            logz.info(f"added : {file_path}")
        logz.info(f"SUCCESS: {zip_path}")   
        
        zip_size_mb = get_file_size_mb(zip_path)
        logz.info(f"Zip size is {zip_size_mb:.2f} MB")
        attach = zip_path if attach_zip and zip_size_mb <= max_zip_size_mb else None
        if attach_zip and zip_size_mb > max_zip_size_mb:
            logz.warning(f"Zip too large than required it's : {zip_size_mb:.2f} MB")
        
        
        
        if email_config:
            body = f"Backup SUCCESS!\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nSources: {source_paths}\nSaved: {zip_path}"
            if attach_zip is not attach:
                body+= f"\nZip not attached due to size limitations. \nBut it's saved in {zip_path}"
            send_email(
                subject=f"BACKUP SUCCESS: {timestamp}",
                body=body,
                to_email=email_config['to'],
                from_email=email_config['from'],
                password=email_config.get('password'),
                oauth_file=email_config.get('oauth_file'),
                attachment=attach  
            )
        return True
    
    except Exception as e:
        logz.error(f"backup failed : {e}") 
                            
                                     
        # FAILURE EMAIL (No attach)
        if email_config:
            body = f"Backup FAILED!\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nSources: {source_paths}\nError: {e}"
            send_email(
                subject=f"BACKUP FAILED: {timestamp}",
                body=body,
                to_email=email_config['to'],
                from_email=email_config['from'],
                password=email_config.get('password'),
                oauth_file=email_config.get('oauth_file')
            )
        return False
        
        
        
        
        
if __name__ == "__main__":
    logz.info("Script started")

    parser = argparse.ArgumentParser(description="Backup with yagmail alerts")
    parser.add_argument('--sources', nargs='+', required=True, help="Files/folders to backup")
    parser.add_argument('--backup_dir', default='./backups', help="Backup directory")
    parser.add_argument('--email-to', help="Recipient email")
    parser.add_argument('--email-from', help="Sender email (Gmail)")
    parser.add_argument('--smtp-password', help="App password (if no OAuth)")
    parser.add_argument('--oauth-file', help="Path to OAuth JSON creds (safer, no password)")
    parser.add_argument('--max-zip-size' , type=float , default= 20, help="max size for the ZIP in Mb")
    parser.add_argument('--attach-zip' , action='store_true' , default=True , help="Attach file or not ?")
    
    
    
    
    args = parser.parse_args()

    email_config = None
    if args.email_to and args.email_from:
        email_config = {
            'to': args.email_to,
            'from': args.email_from,
            'password': args.smtp_password,
            'oauth_file': args.oauth_file
        }

    create_backup(args.sources, args.backup_dir, email_config, args.max_zip_size , args.attach_zip)
    
    