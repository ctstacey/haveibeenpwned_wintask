import time

import csv
import json
import urllib.request               # to download (things from) website(s)

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import logging as l

# imported just to use:  assert(type(fh) == TextIOWrapper)
from io import TextIOWrapper


#=========================================================================
# CONSTANTS AND GLOBAL VARIABLES
#=========================================================================

# CONSTANTS
API               = 'https://haveibeenpwned.com/api/v2/breachedaccount/'
PARAMETERS        = '?includeUnverified=true'
FILENAME          = 'emails_to_check.csv'
CSV_FIRST_ROW     = ['email', 'date_last_pwned']
CSV_FIRST_ROW_STR = 'email,date_last_pwned'            # see CSV_FIRST_ROW


# global VARIABLES
pwndObj = None
pwnage_summary = '\n\n' + \
                 '-'*76 + \
                 '\nSUMMARY:  all info from haveibeenpwned.com\n\n'

  #-----------------------------------------------------------------------
  # SET DEBUG OUTPUT LEVEL
  # https://docs.python.org/3/library/logging.html
  # https://docs.python.org/3/howto/logging.html
  #
  # **********************************************************************
  # ***         NO calls to l.info or l.debug etc. before here         ***
  # ***  else program will silently stop showing any logging messages  ***
  # **********************************************************************

#l.basicConfig(format='%(levelname)s: %(message)s', level=l.DEBUG)
l.basicConfig(format='%(levelname)s: %(message)s', level=l.INFO)

#=========================================================================
# CLASS for opening browser using selenium
#=========================================================================

class SearchPwndAccountsInBrowser:
  
  new_pwnage = False
  
  _driver = None
  _pwned_accounts = []

  def __init__(self):
    pass

  def add_valid_email(s, valid_email) -> None:
    '''add valid email to list of pwned accounts'''
    assert(type(valid_email) == str)

    s.new_pwnage = True
    s._pwned_accounts.append(valid_email)

  def get_driver(s) -> selenium.webdriver:
    '''try to return Firefox or Chrome webdriver
    
       Note: If successful getting a *Chrome* WebDriver, there will be
            an instance of 'chromedriver.exe' that remains open in the
            task manager (Windows OS) even after python ends and the user
            closes the browser window.
            This happens because the variable 'driver' is declared as
            global and is still in scope when python finishes.
            
            This was the only way to keep the (Chrome) browser window open
             after the script had ended.
             Firefox does not have this problem. <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'''

    if s._driver:
      return s._driver
    else:
    
      # try firefox

      try:
        s._driver = webdriver.Firefox(
          executable_path = 'webdrivers/geckodriver(win64,Jan2019).exe')
        return s._driver
      except:
        pass

      # try chrome
      # different chromedrivers work for different versions of Chrome

      # Could not get selenium to pass on chrome options to supress
      # debug output from chromedriver being printed to console

      options = webdriver.ChromeOptions()
      options.add_argument("start-maximized")
      # remove msg 'Chrome is being controlled by automated test software'
      options.add_argument('disable-infobars')
      
      # log is overwriten each time driver starts
      service_log_path = 'webdrivers/chromedriver.log'
      
      try:
        s._driver = webdriver.Chrome \
          (options          = options
          ,executable_path  = 'webdrivers/chromedriver(win32,Jun2019).exe'
          ,service_log_path = service_log_path
          )
        return s._driver
      except:
        pass

      try:
        s._driver = webdriver.Chrome \
          (options          = options
          ,executable_path  = 'webdrivers/chromedriver(win64,Jan2019).exe'
          ,service_log_path = service_log_path
          )
        return s._driver
      except:
        pass
    
      return s._driver


  def try_seach_pwnd_accounts_in_browser(s) -> None:
    '''Try to open a web browser, to open www.haveibeenpwned.com,
       to search each pwned account,
       to show the details of the pwnage to the user.
       On failure, prompts user to search for themselves,
       then continue without error.
    '''
    if (s.new_pwnage):
      try:
        if (not s.get_driver()):
          raise Exception
      
        last = len(s._pwned_accounts) - 1
        
        for i in range(last + 1):
          
          s._driver.get('https://haveibeenpwned.com/')
          assert 'Have I Been Pwned' in s._driver.title

          search_field = s._driver.find_element_by_id('Account')
          search_field.send_keys(s._pwned_accounts[i] + Keys.RETURN)

          _elem = WebDriverWait(s._driver, 120).until(
            EC.presence_of_element_located((By.ID, 'breachDescription'))
          )
          
          if i != last:
            
            # JavaScript cannot control whether a new tab, vs window, gets
            # created. This behaviour is controlled by browser settings.
            # https://stackoverflow.com/questions/4907843/open-a-url-in-
            # a-new-tab-and-not-a-new-window-using-javascript

            w = 'windowName' + str(i+2)
            s._driver.execute_script(f'var _win = window.open("", "{w}")')
            s._driver.switch_to.window(w)

            #s._driver.current_window_handle
            #s._driver.window_handles
        
        s.add_brower_tab_or_window_with_security_warning()
        
        print("Browser should now show one tab/window per pwned account")

      except:
        print('*' * 76
              ,"* ERROR:"
              ,"* Couldn't complete opening a browser to search"
              +" havibeenpwned.com for you."
              ,"* Please search these acounts in www.haveibeenpwned.com :"
              ,'* ' + '\n* '.join(s._pwned_accounts)
              ,'*' * 76
              ,sep = '\n'
              ,flush = True
              )
      
  def add_brower_tab_or_window_with_security_warning(s) -> None:
    '''Output a msg to a new tab/window warning the user not to use these
       window(s) for further browsing as the security settings are likely
       to be different than they normally use. (selenium opens the browser
       in a tesing mode, which is similar visually, but settings differ)
    '''
    # Tried to implement this using a 'javascript alert/confirm box'
    # but the box disappeared after a short time, defeating the purpose.

    if s._driver:

      # JavaScript cannot control whether a new tab, vs window, gets
      # created. This behaviour is controlled by browser settings. 
      # https://stackoverflow.com/questions/4907843/open-a-url-in-
      # a-new-tab-and-not-a-new-window-using-javascript
      
      s._driver.execute_script(
        '''
        var newWin = window.open("")                // blank tab or window

        newWin.document.head.outerHTML =
          ("<head>"
          + "<title>README</title>"
          +"</head>"
          );

        newWin.document.body.outerHTML =
          ("<body>"
          + "<strong>"
          +  "<h1>WARNING:</h1>"
          +  "<p>The browser window(s) just opened are likely to be using"
          +  " different security settings than you normally use.</p>"
          +  "<p>For your own safety, please close the window(s)"
          +  " immediately after you have reviewed the information"
          +  " gathered from www.haveibeenpwned.com"
          +  "<br>"
          +  " (so you don't accidentally continue browsing using"
          +  " different security settings than you normally use).</p>"
          +  "<p>Have a good day and stay safe!</p>"
          + "</strong>"
          +"</body>"
          );

        '''
      )


#=========================================================================
# MAIN
#=========================================================================

def main() -> None:

  global pwndObj
  pwndObj = SearchPwndAccountsInBrowser()
  
  print(f'Checking all emails in {FILENAME} using haveibeenpwned.com')
  
  csv_content = get_csv_content(FILENAME)

  new_csv_list = process_csv_content(csv_content)

  write_new_csv(FILENAME, new_csv_list)

  pwndObj.try_seach_pwnd_accounts_in_browser()

  print(f'{pwnage_summary}')

  print('\nSCRIPT COMPLETED SUCCESSFULLY\n\n'
       +('BUT NEW PWNAGE WAS DETECTED!!!\n' if pwndObj.new_pwnage else '')
       ,flush=True)



def write_new_csv(filename, new_csv_list):
  # add descriptions (first row)
  new_csv_list = [CSV_FIRST_ROW] + new_csv_list

  with try_open_csv(filename, mode='w') as fh:
    csvwriter = csv.writer(fh)
    for row in new_csv_list:
      csvwriter.writerow(row)



def get_csv_content(filename):
  # read-in entire csv contents
  oldcsv = []
  with try_open_csv(filename, mode='r') as fh:
    for row in csv.reader(fh):
      oldcsv.append(row)

  if oldcsv == []:
    #blank csv file
    print(f'The csv "{filename}" appears to be empty.\n'
           'Each line (of the csv file) should start with a valid email'
           ' address.\n'
           'Optionally followed by the last pawnage date'
           ' (in format yyyy-mm-dd).\n'
           'Also Optional: first line exactly as in example below.\n'
           'Note: no spaces on any lines.\n'
           'example file:\n'
          f'   {CSV_FIRST_ROW_STR}\n'
           '   example1@hotmail.com,2018-12-31\n'
           '   example2@hotmail.com\n'
           'Fix the file then try again.')
    input('press enter to exit')
    raise SystemExit

  # strip descriptions (first row) if exist
  if oldcsv[0] == CSV_FIRST_ROW:                            # list == list
    oldcsv = oldcsv[1:]

  # limit number of emails (lines)  (so we don't abuse haveibeenpwned.com)
  if len(oldcsv) > 20:
    print( 'WARNING: THIS PROGRAM WILL ONLY CHECK THE FIRST 20 EMAIL\n'
          f'ADDRESSES FROM "{FILENAME}" (incl. blank/malformed lines)\n'
           'FURTHERMORE, IF YOU CONTINUE, THE EXCESS EMAIL ADDRESSES\n'
           'WILL BE DELETED FROM THE FILE.')
    try:
      yn = input('do you want to continue (y/n):')
      if yn in 'yY':
        oldcsv = oldcsv[0:20]
      else:
        raise SystemExit                        # drops through to except:
    except:
      print(f'Exiting without editing the file.')
      raise SystemExit

  l.debug(f'csv file contents:\n{oldcsv}')

  # returns list of lists containing entire csv content
  return oldcsv


def process_csv_content(csv_content) -> list:

  global pwnage_summary
  global pwndObj

  newcsv = []
  for line in csv_content:

    if len(line) == 1:
      email                = line[0]
      old_last_pwnage_date = None

    elif len(line) == 2:
      email                = line[0]
      old_last_pwnage_date = line[1]

    elif len(line) == 0:
      l.debug('skipping blank csv line')
      continue

    elif len(line) > 2:
      print(f'skipping ill formatted csv line (but still keeping it'
            f' in the csv file):\n"{line}"')
      newcsv.append(line)
      continue

    new_last_pwnage_date = process(email)

    if new_last_pwnage_date == None:
      pwnage_summary += f'{email}  no pwnage ever.\n'
      newcsv.append([email])
    else:
      newcsv.append([email, new_last_pwnage_date])

      if new_last_pwnage_date == old_last_pwnage_date:
        pwnage_summary += \
          f'{email}  no new pwnage. (last was {new_last_pwnage_date})\n'
      else:
        pwndObj.add_valid_email(email)

        pwnage_summary += \
          f'{email}  ****** DANGER, NEW PWNAGE FOUND ******\n' + \
           ' '*len(email) + '  (see output above for instructions!!!)\n'

        print('*'*76
             , '* Oh no - NEW pwnage found!'
             ,f"* We will try to open a browser to search {email} in"
             + " haveibeenpwned.com for you."
             , '* IMPORTANT:'
             , '* PLEASE CHANGE YOUR PASSWORD FOR THIS ACCOUNT ASAP'
             , '* (AND ANY OTHER ACCOUNT THAT USE THE SAME PASSWORD)'
             , '*'*76
             , sep = '\n'
             )
          
  # returns a list (ready to be written to csv file by csv.writer)
  return newcsv


def process(email) -> str:
  # recieves a byte string
  http_json_response = get_pwnage_fm_haveibeenpwned(email)

  if http_json_response:
    most_recent_breach_date = \
      get_most_recent_breach_date(http_json_response)
    print( 'most_recent_breach_date ='
          f' {most_recent_breach_date} (yyyy-mm-dd)')
    return most_recent_breach_date
  else:
    # no pwnage found
    print('no pwnage found')
    return None



def get_most_recent_breach_date(http_json_response) -> str:
  ''' relies on USA dates (ie yyyy-mm-dd) so it sorts as expected
  '''
  
  # load (byte string) json into Python as a dictionary
  dict_of_json = json.loads(http_json_response)
  
  breach_dates = []
  for breach in dict_of_json:
    breach_dates.append(breach['BreachDate'])

  l.debug(f'all breach dates (sorted):\n{sorted(breach_dates)}')

  return sorted(breach_dates)[-1]



def try_open_csv(filepath, mode='r') -> TextIOWrapper:
  ''' A wrapper for open(). Produces user friendly error message if
      file cannot be found, and normal messages for all other errors '''
  assert(type(filepath) == str)

  # must open csv file object using "newline=''" else newlines within
  # quotes will not be handled correctly, and writing to csv file on
  # system that writes \r\n will have another \r added thus mucking it up.
  # https://docs.python.org/3/library/csv.html?highlight=csv#id3
  try:
    fh = open(filepath, mode=mode, newline='')
  except FileNotFoundError:
    print(f'The file "{filepath}" could not be found.'
           ' Please check you have included the file extension'
           ' and the file exists. Then try again.')
    input('press enter to exit')
    raise SystemExit

  # other exceptions drop through to be handled by other (normal) handlers

  return fh

# I did try to use www.haveibeenpwned.com publicly advertised API
# https://haveibeenpwned.com/API/v2#BreachesForAccount
# but got blocked by their proxy, which must have decided that I was a bot
# or something. So after some digging, I found that that their main
# webpage uses its own API url to get the pwnage info for the address
# the user submits manually, then it uses JS to edit the page to include
# the returned pwnage info. So I just used the same API their main
# webpage does, and parsed the returned json to get the last pwned date
# out (done in another function).
def get_pwnage_fm_haveibeenpwned(valid_email) -> bytes:
  '''
  will only read 200000 characters (~20KB file)
  returns: BYTE string containing HTTP response body.
  quits with user message if things go wrong.

  Three second delay added after each API access.
  (haveibeenpwned.com limits API access to once per 1500ms)
  '''
  assert(type(valid_email) == str)
  print(f'querying haveibeenpwned.com regarding {valid_email}')

  # haveibeenpwned.com limits API requests to one every 1500ms.
  time.sleep(3)

  url = API + valid_email + PARAMETERS

  try:
    req = urllib.request.Request(url    = url
                                ,data   = None
                                ,method = 'GET'
                                )
    # haveibeenpwned.com API requires a User-Agent header.
    req.add_header('User-Agent', 'basic-pwnage-check')

    r = urllib.request.urlopen(req)

    print(f'recieved HTTP response: {r.status} {r.reason}')     #ie 200 OK

    # byte string
    data = r.read(200000)

    if len(data) > 199999:             #test that entire download was read
      print('LIMIT EXCEEDED: FILE RETURNED WAS TOO LARGE.\nExiting now.')
      raise SystemExit                          # falls through to except:

  # if 200 continue, if 404 then no pwnage, all else, raise error & exit
  except urllib.error.HTTPError as e:
    l.debug(f'HTTP response code: {e.code}')
    l.debug(f'HTTP response:\n{e.read()}')
    if e.code == 404:
      l.debug('404 hence, no pwnage found')
      return None                                        # no pwnage found
    else:
      raise e
  
  except:
    print(f'Error while trying to send HTTP GET request to "{url}".'
           ' Check internet connection and try again.')
    input('press enter to exit')
    raise SystemExit

  #exit if download did not come from the url specified in this script
  if r.geturl() != url:
    print('source information appears to have come from another url than'
          ' was specified in the script. This could be because of an'
          ' innocent redirect was used (server side), or because of other'
          ' more sinister reason. Please check source url, modify script'
          ' accordingly, and re-run.')
    input('press enter to exit')
    raise SystemExit

  l.debug("before returning HTTP response, type(data) = ", type(data))
  l.debug(f'all data downloaded:\n{data}')

  return data




#=========================================================================
# FINALLY

# This should be the ONLY TOP LEVEL CODE IN THIS SOURCE FILE!
# Every function above this function has already been interpreted,
# so is available to be called by main().
#
# Conditional execution of main() (ie top level code) also makes it
# possible to import this file into other files.
# (ie. when this file is imported, __name__ will be set to the name of
#  the source file, not set to '__main__')
#
# Python itself does not use a main() function. Instead, Python eagerly
# interpretes any file thrown at it. So when you run/import a file, all
# functions are defined and interpreted, and top level code is executed.
if __name__ == '__main__':
  main()


##########################################################################
#   END OF FILE
##########################################################################