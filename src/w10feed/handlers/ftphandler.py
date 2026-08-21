from ftplib import FTP, all_errors
from datetime import datetime
import os

class FTPHandler:
    def __init__(self, host, user, password):
        self.ftp = FTP(host, user, password)
        self.ftp.encoding = 'utf-8'
        self.ftp.sock.settimeout(15)
        self.ERRORS = all_errors
    def cd(self, path):
        self.ftp.cwd(path)

    def list_files(self, path, pattern=""):
        files = []
        try:
            self.ftp.cwd(path)
            lines = []
            self.ftp.retrlines('LIST', lines.append)
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 9 and parts[0][0] != "d":
                    filename = ' '.join(parts[8:])
                    if filename.endswith(pattern):
                        # MMM DD HH:MM or MMM DD YYYY
                        try:
                            mtime = self._parse_list_time(line)
                            files.append({
                                'name': filename,
                                'mtime': mtime,
                                'path': f"{path}/{filename}"
                            })
                        except:
                            pass
        except all_errors:
            pass
        return sorted(files, key=lambda x: x['mtime'], reverse=True)
    
    def list_dirs(self, path):
        """Get list of directories in path"""
        dirs = []
        try:
            self.ftp.cwd(path)
            lines = []
            self.ftp.retrlines('LIST', lines.append)
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 9 and parts[0][0] == 'd' and parts[8][0] != '.':
                    dirname = ' '.join(parts[8:])
                    dirs.append(dirname)
        except all_errors:
            pass
        return dirs
    
    def _parse_list_time(self, line):
        # based on ftp.w10.host server
        parts = line.split()
        month_str = parts[5]
        day = parts[6]
        time_or_year = parts[7]
        
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = months.get(month_str, 1)
        day = int(day)
        
        if ':' in time_or_year:
            # This year
            hour, minute = map(int, time_or_year.split(':'))
            year = datetime.now().year
            second = 0
        else:
            # prevew year
            year = int(time_or_year)
            hour = minute = second = 0
        
        dt = datetime(year, month, day, hour, minute, second)
        return int(dt.timestamp())
    
    def read_file(self, path):
        data = []
        try:
            self.ftp.retrbinary(f'RETR {path}', data.append)
            return b''.join(data).decode('utf-8', errors='ignore')
        except all_errors:
            return None

    def upload_file(self, local_path, remote_path):
        try:
            if not os.path.exists(local_path):
                print(f"Error: local {local_path} not found")
                return False
            
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_dir(remote_dir)
            
            self.ftp.cwd(remote_dir)
            with open(local_path, 'rb') as file:
                cmd = f'STOR {remote_path}'
                self.ftp.storbinary(cmd, file)
            
            print(f"File uploaded: {remote_path}")
            return True
            
        except FileNotFoundError:
            print(f"Error: file {local_path} not found")
            return False
        except all_errors as e:
            print(f"FTP error: {e}")
            return False
        except Exception as e:
            print(f"Error: {e}")
            return False

    def _ensure_remote_dir(self, remote_dir):
        try:
            self.ftp.cwd(remote_dir)
            self.ftp.cwd('..')
        except all_errors:
            # creating a missing directory
            try:
                self.ftp.mkd(remote_dir)
            except all_errors as e:
                print(f"Warning: {remote_dir} doesn't create: {e}")
    
    def test_connection(self, debug=False):
        try:
            current_dir = self.ftp.pwd()
            if debug:
                print("Connection active.")
                print(f"PWD: {current_dir}")
            
            # Trying make test file
            test_file = f'/test_{int(datetime.now().timestamp())}.txt'
            self.ftp.storbinary(f'STOR {test_file}', open(__file__, 'rb'))
            
            if self.ftp.size(test_file):
                self.ftp.delete(test_file)
                if debug:
                    print(f"Write access rights confirmed.")
                return True
            
        except all_errors as e:
            print(f"Error: {e}")
            return False
    
    def close(self):
        self.ftp.quit()