"""Install exception handler for process crash."""
import os
import sys
import json
from subprocess import check_output
from selfdrive.version import version, dirty

from selfdrive.swaglog import cloudlog

if os.getenv("NOLOG") or os.getenv("NOCRASH"):
  def capture_exception(*exc_info):
    pass
  def bind_user(**kwargs):
    pass
  def bind_extra(**kwargs):
    pass
  def install():
    pass
else:
  from raven import Client
  from raven.transport.http import HTTPTransport

  error_tags = {'dirty': dirty}

  try:
    with open("/data/data/ai.comma.plus.offroad/files/persistStore/persist-auth", "r") as f:
      auth = json.loads(f.read())
    auth = json.loads(auth['commaUser'])
    error_tags['username'] = auth['username']
    error_tags['email'] = auth['email']
  except:
    pass

  try:
    out = check_output(["git", "branch"]).decode("utf8")
    current_branch = next(line for line in out.split("\n") if line.startswith("*")).strip("*").strip()
    error_tags['branch'] = current_branch
  except:
    pass

  client = Client('https://137e8e621f114f858f4c392c52e18c6d:8aba82f49af040c8aac45e95a8484970@sentry.io/1404547',
                  install_sys_hook=False, transport=HTTPTransport, release=version, tags=error_tags)

  def capture_exception(*args, **kwargs):
    client.captureException(*args, **kwargs)
    cloudlog.error("crash", exc_info=kwargs.get('exc_info', 1))

  def capture_warning(warning_string):
    client.captureMessage(warning_string, level='warning')
  
  def capture_info(info_string):
    client.captureMessage(info_string, level='info')

  def bind_user(**kwargs):
    client.user_context(kwargs)

  def bind_extra(**kwargs):
    client.extra_context(kwargs)

  def install():
    # installs a sys.excepthook
    __excepthook__ = sys.excepthook
    def handle_exception(*exc_info):
      if exc_info[0] not in (KeyboardInterrupt, SystemExit):
        capture_exception(exc_info=exc_info)
      __excepthook__(*exc_info)
    sys.excepthook = handle_exception
