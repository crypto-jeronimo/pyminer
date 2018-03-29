# The MIT License (MIT)
#
# Copyright (c) 2014 Richard Moore
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import binascii, json, hashlib, socket, struct, sys, threading, time, urlparse


USER_AGENT = "PyMiner"
VERSION = [0, 1]


# Which algorithm for proof-of-work to use
ALGORITHM_SCRYPT      = 'scrypt'
ALGORITHM_SHA256D     = 'sha256d'
ALGORITHM_YESCRYPT    = 'yescrypt'

ALGORITHMS = [ ALGORITHM_SCRYPT, ALGORITHM_SHA256D, ALGORITHM_YESCRYPT ]


# Verbosity and log level
QUIET           = False
DEBUG           = False
DEBUG_PROTOCOL  = False

LEVEL_PROTOCOL  = 'protocol'
LEVEL_INFO      = 'info'
LEVEL_DEBUG     = 'debug'
LEVEL_ERROR     = 'error'


# These control which scrypt implementation to use
SCRYPT_LIBRARY_C = 'scrypt (https://github.com/forrestv/p2pool)'
SCRYPT_LIBRARIES = [ SCRYPT_LIBRARY_C ]

YESCRYPT_LIBRARY_C      = 'https://password-hashing.net/submissions/yescrypt-v1.tar.gz'
YESCRYPT_LIBRARIES = [ YESCRYPT_LIBRARY_C ]

WELCOME_MSG = ("If you have found this software useful and would like to support its future\n"
               "development, please, feel free to donate:\n\n"
               "   BTC: 1HKWV5t4KGUwybVHNUaaY9TXFSoBvoaSiP\n"
               "   ETH: 0xF17e490B391E17BE2D14BFfaA831ab8966d2e689\n"
               "   LTC: LNSEJzT8byYasZGd4f9c3DgtMbmexnXHdy\n"
               "   BCH: 1AVXvPBrNdhTdwBN5VQT5LSHa7sEzMSia4\n"
               "   XEM: NB3NDXRBOLEJLPT6MP6JAD4EZEOX5TFLDG3WR7JJ\n"
               "   MONA: MPq54r8XTwtB2qmAeVqayy27ZCaPt845B6\n"
               "   KOTO: k1GHJkvxLQocac94MFBbKAsdUvNbFdFWUyE\n"
               "   NEET: NYaP7eEsDdALK5eHPZkYk1d8pBLyGvq9L1\n\n"
               "Happy mining!")

def log(message, level):
  '''Conditionally write a message to stdout based on command line options and level.'''

  global DEBUG
  global DEBUG_PROTOCOL
  global QUIET

  if QUIET and level != LEVEL_ERROR: return
  if not DEBUG_PROTOCOL and level == LEVEL_PROTOCOL: return
  if not DEBUG and level == LEVEL_DEBUG: return

  if level != LEVEL_PROTOCOL: message = '[%s] %s' % (level.upper(), message)

  print ("[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message))


# Convert from/to binary and hexidecimal strings (could be replaced with .encode('hex') and .decode('hex'))
hexlify = binascii.hexlify
unhexlify = binascii.unhexlify


def sha256d(message):
  '''Double SHA256 Hashing function.'''

  return hashlib.sha256(hashlib.sha256(message).digest()).digest()


def swap_endian_word(hex_word):
  '''Swaps the endianness of a hexidecimal string of a word and converts to a binary string.'''

  message = unhexlify(hex_word)
  if len(message) != 4: raise ValueError('Must be 4-byte word')
  return message[::-1]


def swap_endian_words(hex_words):
  '''Swaps the endianness of a hexidecimal string of words and converts to binary string.'''

  message = unhexlify(hex_words)
  if len(message) % 4 != 0: raise ValueError('Must be 4-byte word aligned')
  return ''.join([ message[4 * i: 4 * i + 4][::-1] for i in range(0, len(message) // 4) ])


def human_readable_hashrate(hashrate):
  '''Returns a human readable representation of hashrate.'''

  if hashrate < 1000:
    return '%2f hashes/s' % hashrate
  if hashrate < 10000000:
    return '%2f khashes/s' % (hashrate / 1000)
  if hashrate < 10000000000:
    return '%2f Mhashes/s' % (hashrate / 1000000)
  return '%2f Ghashes/s' % (hashrate / 1000000000)


SCRYPT_LIBRARY = None
scrypt_proof_of_work = None
def set_scrypt_library():
  '''Sets the scrypt library implementation to use.'''

  global SCRYPT_LIBRARY
  global scrypt_proof_of_work

  import scrypt
  scrypt_proof_of_work = scrypt.getPoWHash
  SCRYPT_LIBRARY = SCRYPT_LIBRARY_C

set_scrypt_library()


class Job(object):
  '''Encapsulates a Job from the network and necessary helper methods to mine.

     "If you have a procedure with 10 parameters, you probably missed some."
           ~Alan Perlis
  '''

  def __init__(
    self,
    job_id,
    prevhash,
    coinb1,
    coinb2,
    merkle_branches,
    version,
    nbits,
    ntime,
    target,
    extranonce1,
    extranonce2_size,
    proof_of_work,
    max_nonce=0x7fffffff,
  ):

    # Job parts from the mining.notify command
    self._job_id = job_id
    self._prevhash = prevhash
    self._coinb1 = coinb1
    self._coinb2 = coinb2
    self._merkle_branches = [ b for b in merkle_branches ]
    self._version = version
    self._nbits = nbits
    self._ntime = ntime

    self._max_nonce = max_nonce

    # Job information needed to mine from mining.subsribe
    self._target = target
    self._extranonce1 = extranonce1
    self._extranonce2_size = extranonce2_size

    # Proof of work algorithm
    self._proof_of_work = proof_of_work

    # Flag to stop this job's mine coroutine
    self._done = False

    # Hash metrics (start time, delta time, total hashes)
    self._dt = 0.0
    self._hash_count = 0

  # Accessors
  id = property(lambda s: s._job_id)
  prevhash = property(lambda s: s._prevhash)
  coinb1 = property(lambda s: s._coinb1)
  coinb2 = property(lambda s: s._coinb2)
  merkle_branches = property(lambda s: [ b for b in s._merkle_branches ])
  version = property(lambda s: s._version)
  nbits = property(lambda s: s._nbits)
  ntime = property(lambda s: s._ntime)

  target = property(lambda s: s._target)
  extranonce1 = property(lambda s: s._extranonce1)
  extranonce2_size = property(lambda s: s._extranonce2_size)

  proof_of_work = property(lambda s: s._proof_of_work)


  @property
  def hashrate(self):
    '''The current hashrate, or if stopped hashrate for the job's lifetime.'''

    if self._dt == 0: return 0.0
    return self._hash_count / self._dt


  def merkle_root_bin(self, extranonce2_bin):
    '''Builds a merkle root from the merkle tree'''

    coinbase_bin = unhexlify(self._coinb1) + unhexlify(self._extranonce1) + extranonce2_bin + unhexlify(self._coinb2)
    coinbase_hash_bin = sha256d(coinbase_bin)

    merkle_root = coinbase_hash_bin
    for branch in self._merkle_branches:
      merkle_root = sha256d(merkle_root + unhexlify(branch))
    return merkle_root


  def stop(self):
    '''Requests the mine coroutine stop after its current iteration.'''

    self._done = True


  def mine(self, nonce_start=0, nonce_stride=1):
    '''Returns an iterator that iterates over valid proof-of-work shares.

       This is a co-routine; that takes a LONG time; the calling thread should look like:

         for result in job.mine(self):
           submit_work(result)

       nonce_start and nonce_stride are useful for multi-processing if you would like
       to assign each process a different starting nonce (0, 1, 2, ...) and a stride
       equal to the number of processes.
    '''

    t0 = time.time()

    # @TODO: test for extranonce != 0... Do I reverse it or not?
    for extranonce2 in xrange(self._max_nonce):

      # Must be unique for any given job id, according to http://mining.bitcoin.cz/stratum-mining/ but never seems enforced?
      extranonce2_bin = struct.pack('<I', extranonce2)

      merkle_root_bin = self.merkle_root_bin(extranonce2_bin)
      header_prefix_bin = swap_endian_word(self._version) + swap_endian_words(self._prevhash) + merkle_root_bin + swap_endian_word(self._ntime) + swap_endian_word(self._nbits)
      for nonce in xrange(nonce_start, self._max_nonce, nonce_stride):
        # This job has been asked to stop
        if self._done:
          self._dt += (time.time() - t0)
          raise StopIteration()

        # Proof-of-work attempt
        nonce_bin = struct.pack('<I', nonce)
        pow = self.proof_of_work(header_prefix_bin + nonce_bin)[::-1].encode('hex')

        # Did we reach or exceed our target?
        if pow <= self.target:
          result = dict(
            job_id = self.id,
            extranonce2 = hexlify(extranonce2_bin),
            ntime = str(self._ntime),                    # Convert to str from json unicode
            nonce = hexlify(nonce_bin[::-1])
          )
          self._dt += (time.time() - t0)

          yield result

          t0 = time.time()

        self._hash_count += 1


  def __str__(self):
    return '<Job id=%s prevhash=%s coinb1=%s coinb2=%s merkle_branches=%s version=%s nbits=%s ntime=%s target=%s extranonce1=%s extranonce2_size=%d>' % (self.id, self.prevhash, self.coinb1, self.coinb2, self.merkle_branches, self.version, self.nbits, self.ntime, self.target, self.extranonce1, self.extranonce2_size)


# Subscription state
class Subscription(object):
  '''Encapsulates the Subscription state from the JSON-RPC server'''

  _max_nonce = None

  # Subclasses should override this
  def ProofOfWork(header):
    raise Exception('Do not use the Subscription class directly, subclass it')

  class StateException(Exception): pass

  def __init__(self):
    self._id = None
    self._difficulty = None
    self._extranonce1 = None
    self._extranonce2_size = None
    self._target = None
    self._worker_name = None

    self._mining_thread = None

  # Accessors
  id = property(lambda s: s._id)
  worker_name = property(lambda s: s._worker_name)

  difficulty = property(lambda s: s._difficulty)
  target = property(lambda s: s._target)

  extranonce1 = property(lambda s: s._extranonce1)
  extranonce2_size = property(lambda s: s._extranonce2_size)


  def set_worker_name(self, worker_name):
    if self._worker_name:
      raise self.StateException('Already authenticated as %r (requesting %r)' % (self._username, username))

    self._worker_name = worker_name


  def _set_target(self, target):
    self._target = '%064x' % target


  def set_difficulty(self, difficulty):
    if difficulty < 0: raise self.StateException('Difficulty must be non-negative')

    # Compute target
    if difficulty == 0:
      target = 2 ** 256 - 1
    else:
      target = min(int((0xffff0000 * 2 ** (256 - 64) + 1) / difficulty - 1 + 0.5), 2 ** 256 - 1)

    self._difficulty = difficulty
    self._set_target(target)


  def set_subscription(self, subscription_id, extranonce1, extranonce2_size):
    if self._id is not None:
      raise self.StateException('Already subscribed')

    self._id = subscription_id
    self._extranonce1 = extranonce1
    self._extranonce2_size = extranonce2_size


  def create_job(self, job_id, prevhash, coinb1, coinb2, merkle_branches, version, nbits, ntime):
    '''Creates a new Job object populated with all the goodness it needs to mine.'''

    if self._id is None:
      raise self.StateException('Not subscribed')

    return Job(
      job_id=job_id,
      prevhash=prevhash,
      coinb1=coinb1,
      coinb2=coinb2,
      merkle_branches=merkle_branches,
      version=version,
      nbits=nbits,
      ntime=ntime,
      target=self.target,
      extranonce1=self._extranonce1,
      extranonce2_size=self.extranonce2_size,
      proof_of_work=self.ProofOfWork,
      max_nonce=self._max_nonce,
    )


  def __str__(self):
    return '<Subscription id=%s, extranonce1=%s, extranonce2_size=%d, difficulty=%d worker_name=%s>' % (self.id, self.extranonce1, self.extranonce2_size, self.difficulty, self.worker_name)


class SubscriptionScrypt(Subscription):
  '''Subscription for Scrypt-based coins, like Litecoin.'''

  ProofOfWork = lambda s, h: scrypt_proof_of_work(h)
  _max_nonce = 0x7fffffff

  def _set_target(self, target):
    # Why multiply by 2**16? See: https://litecoin.info/Mining_pool_comparison
    self._target = '%064x' % (target << 16)


class SubscriptionSHA256D(Subscription):
  '''Subscription for Double-SHA256-based coins, like Bitcoin.'''

  ProofOfWork = sha256d


class SubscriptionYescrypt(Subscription):
  '''Subscription for Yescrypt-based coins.'''

  import yescrypt
  ProofOfWork = yescrypt.getPoWHash
  _max_nonce = 0x3fffff

  def _set_target(self, target):
    self._target = '%064x' % (target << 16)


# Maps algorithms to their respective subscription objects
SubscriptionByAlgorithm = {
  ALGORITHM_SCRYPT: SubscriptionScrypt,
  ALGORITHM_SHA256D: SubscriptionSHA256D,
  ALGORITHM_YESCRYPT: SubscriptionYescrypt,
}


class SimpleJsonRpcClient(object):
  '''Simple JSON-RPC client.

    To use this class:
      1) Create a sub-class
      2) Override handle_reply(self, request, reply)
      3) Call connect(socket)

    Use self.send(method, params) to send JSON-RPC commands to the server.

    A new thread is created for listening to the connection; so calls to handle_reply
    are synchronized. It is safe to call send from withing handle_reply.
  '''

  class ClientException(Exception): pass

  class RequestReplyException(Exception):
    def __init__(self, message, reply, request = None):
      Exception.__init__(self, message)
      self._reply = reply
      self._request = request

    request = property(lambda s: s._request)
    reply = property(lambda s: s._reply)

  class RequestReplyWarning(RequestReplyException):
    '''Sub-classes can raise this to inform the user of JSON-RPC server issues.'''
    pass

  def __init__(self):
    self._socket = None
    self._lock = threading.RLock()
    self._rpc_thread = None
    self._message_id = 1
    self._requests = dict()


  def _handle_incoming_rpc(self):
    data = ""
    while True:
      # Get the next line if we have one, otherwise, read and block
      if '\n' in data:
        (line, data) = data.split('\n', 1)
      else:
        chunk = self._socket.recv(1024)
        data += chunk
        continue

      log('JSON-RPC Server > ' + line, LEVEL_PROTOCOL)

      # Parse the JSON
      try:
        reply = json.loads(line)
      except Exception, e:
        log("JSON-RPC Error: Failed to parse JSON %r (skipping)" % line, LEVEL_ERROR)
        continue

      try:
        request = None
        with self._lock:
          if 'id' in reply and reply['id'] in self._requests:
            request = self._requests[reply['id']]
          self.handle_reply(request = request, reply = reply)
      except self.RequestReplyWarning, e:
        output = e.message
        if e.request:
          try:
            output += '\n  ' + e.request
          except TypeError:
            output += '\n  ' + str(e.request)
        output += '\n  ' + e.reply
        log(output, LEVEL_ERROR)


  def handle_reply(self, request, reply):
    # Override this method in sub-classes to handle a message from the server
    raise self.RequestReplyWarning('Override this method')


  def send(self, method, params):
    '''Sends a message to the JSON-RPC server'''

    if not self._socket:
      raise self.ClientException('Not connected')

    request = dict(id = self._message_id, method = method, params = params)
    message = json.dumps(request)
    with self._lock:
      self._requests[self._message_id] = request
      self._message_id += 1
      self._socket.send(message + '\n')

    log('JSON-RPC Server < ' + message, LEVEL_PROTOCOL)

    return request


  def connect(self, socket):
    '''Connects to a remove JSON-RPC server'''

    if self._rpc_thread:
      raise self.ClientException('Already connected')

    self._socket = socket

    self._rpc_thread = threading.Thread(target = self._handle_incoming_rpc)
    self._rpc_thread.daemon = True
    self._rpc_thread.start()


# Miner client
class Miner(SimpleJsonRpcClient):
  '''Simple mining client'''

  class MinerWarning(SimpleJsonRpcClient.RequestReplyWarning):
    def __init__(self, message, reply, request = None):
      SimpleJsonRpcClient.RequestReplyWarning.__init__(self, 'Mining Sate Error: ' + message, reply, request)

  class MinerAuthenticationException(SimpleJsonRpcClient.RequestReplyException): pass

  def __init__(self, url, username, password, algorithm=ALGORITHM_YESCRYPT):
    SimpleJsonRpcClient.__init__(self)

    self._url = url
    self._username = username
    self._password = password

    self._subscription = SubscriptionByAlgorithm[algorithm]()

    self._job = None

    self._accepted_shares = 0

  # Accessors
  url = property(lambda s: s._url)
  username = property(lambda s: s._username)
  password = property(lambda s: s._password)


  # Overridden from SimpleJsonRpcClient
  def handle_reply(self, request, reply):

    # New work, stop what we were doing before, and start on this.
    if reply.get('method') == 'mining.notify':
      if 'params' not in reply or len(reply['params']) != 9:
        raise self.MinerWarning('Malformed mining.notify message', reply)

      (job_id, prevhash, coinb1, coinb2, merkle_branches, version, nbits, ntime, clean_jobs) = reply['params']
      self._spawn_job_thread(job_id, prevhash, coinb1, coinb2, merkle_branches, version, nbits, ntime)

      log('New job: job_id=%s' % job_id, LEVEL_DEBUG)

    # The server wants us to change our difficulty (on all *future* work)
    elif reply.get('method') == 'mining.set_difficulty':
      if 'params' not in reply or len(reply['params']) != 1:
        raise self.MinerWarning('Malformed mining.set_difficulty message', reply)

      (difficulty, ) = reply['params']
      self._subscription.set_difficulty(difficulty)

      log('Change difficulty: difficulty=%s' % difficulty, LEVEL_DEBUG)

    # This is a reply to...
    elif request:

      # ...subscribe; set-up the work and request authorization
      if request.get('method') == 'mining.subscribe':
        if 'result' not in reply or len(reply['result']) != 3 or len(reply['result'][0]) != 2:
          raise self.MinerWarning('Reply to mining.subscribe is malformed', reply, request)

        ((mining_notify, subscription_id), extranonce1, extranonce2_size) = reply['result']

        self._subscription.set_subscription(subscription_id, extranonce1, extranonce2_size)

        log('Subscribed: subscription_id=%s' % subscription_id, LEVEL_DEBUG)

        # Request authentication
        self.send(method = 'mining.authorize', params = [ self.username, self.password ])

      # ...authorize; if we failed to authorize, quit
      elif request.get('method') == 'mining.authorize':
        if 'result' not in reply or not reply['result']:
          raise self.MinerAuthenticationException('Failed to authenticate worker', reply, request)

        worker_name = request['params'][0]
        self._subscription.set_worker_name(worker_name)

        log('Authorized: worker_name=%s' % worker_name, LEVEL_DEBUG)

      # ...submit; complain if the server didn't accept our submission
      elif request.get('method') == 'mining.submit':
        if 'result' not in reply or not reply['result']:
          log('Share - Invalid', LEVEL_INFO)
          raise self.MinerWarning('Failed to accept submit', reply, request)

        self._accepted_shares += 1
        log('Accepted shares: %d' % self._accepted_shares, LEVEL_INFO)

      # ??? *shrug*
      else:
        raise self.MinerWarning('Unhandled message', reply, request)

    # ??? *double shrug*
    else:
      raise self.MinerWarning('Bad message state', reply)


  def _spawn_job_thread(self, job_id, prevhash, coinb1, coinb2, merkle_branches, version, nbits, ntime):
    '''Stops any previous job and begins a new job.'''

    # Stop the old job (if any)
    if self._job: self._job.stop()

    # Create the new job
    self._job = self._subscription.create_job(
      job_id = job_id,
      prevhash = prevhash,
      coinb1 = coinb1,
      coinb2 = coinb2,
      merkle_branches = merkle_branches,
      version = version,
      nbits = nbits,
      ntime = ntime
    )

    def run(job):
      try:
        for result in job.mine():
          params = [ self._subscription.worker_name ] + [ result[k] for k in ('job_id', 'extranonce2', 'ntime', 'nonce') ]
          self.send(method = 'mining.submit', params = params)
          log("Found share: " + str(params), LEVEL_INFO)
        log("Hashrate: %s" % human_readable_hashrate(job.hashrate), LEVEL_INFO)
      except Exception, e:
        log("ERROR: %s" % e, LEVEL_ERROR)

    thread = threading.Thread(target = run, args = (self._job, ))
    thread.daemon = True
    thread.start()

  @staticmethod
  def welcome_msg():
    log(WELCOME_MSG, LEVEL_INFO)


  def serve_forever(self):
    '''Begins the miner. This method does not return.'''

    # Figure out the hostname and port
    url = urlparse.urlparse(self.url)
    hostname = url.hostname or ''
    port = url.port or 9333

    self.welcome_msg()

    log('Starting server on %s:%d' % (hostname, port), LEVEL_INFO)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((hostname, port))
    self.connect(sock)

    self.send(method = 'mining.subscribe', params = [ "%s/%s" % (USER_AGENT, '.'.join(str(p) for p in VERSION)) ])

    # Forever...
    while True:
      time.sleep(10)


def test_subscription():
  '''Test harness for mining, using a known valid share.'''

  log('TEST: Scrypt algorithm = %r' % SCRYPT_LIBRARY, LEVEL_DEBUG)
  log('TEST: Testing Subscription', LEVEL_DEBUG)

  subscription = SubscriptionScrypt()

  # Set up the subscription
  reply = json.loads('{"error": null, "id": 1, "result": [["mining.notify", "ae6812eb4cd7735a302a8a9dd95cf71f"], "f800880e", 4]}')
  log('TEST: %r' % reply, LEVEL_DEBUG)
  ((mining_notify, subscription_id), extranonce1, extranonce2_size) = reply['result']
  subscription.set_subscription(subscription_id, extranonce1, extranonce2_size)

  # Set the difficulty
  reply = json.loads('{"params": [32], "id": null, "method": "mining.set_difficulty"}')
  log('TEST: %r' % reply, LEVEL_DEBUG)
  (difficulty, ) = reply['params']
  subscription.set_difficulty(difficulty)

  # Create a job
  reply = json.loads('{"params": ["1db7", "0b29bfff96c5dc08ee65e63d7b7bab431745b089ff0cf95b49a1631e1d2f9f31", "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff2503777d07062f503253482f0405b8c75208", "0b2f436f696e48756e74722f0000000001603f352a010000001976a914c633315d376c20a973a758f7422d67f7bfed9c5888ac00000000", ["f0dbca1ee1a9f6388d07d97c1ab0de0e41acdf2edac4b95780ba0a1ec14103b3", "8e43fd2988ac40c5d97702b7e5ccdf5b06d58f0e0d323f74dd5082232c1aedf7", "1177601320ac928b8c145d771dae78a3901a089fa4aca8def01cbff747355818", "9f64f3b0d9edddb14be6f71c3ac2e80455916e207ffc003316c6a515452aa7b4", "2d0b54af60fad4ae59ec02031f661d026f2bb95e2eeb1e6657a35036c017c595"], "00000002", "1b148272", "52c7b81a", true], "id": null, "method": "mining.notify"}')
  log('TEST: %r' % reply, LEVEL_DEBUG)
  (job_id, prevhash, coinb1, coinb2, merkle_branches, version, nbits, ntime, clean_jobs) = reply['params']
  job = subscription.create_job(
    job_id = job_id,
    prevhash = prevhash,
    coinb1 = coinb1,
    coinb2 = coinb2,
    merkle_branches = merkle_branches,
    version = version,
    nbits = nbits,
    ntime = ntime
  )

  # Scan that job (if I broke something, this will run for a long time))
  for result in job.mine(nonce_start = 1210450368 - 3):
    log('TEST: found share - %r' % repr(result), LEVEL_DEBUG)
    break

  valid = { 'ntime': '52c7b81a', 'nonce': '482601c0', 'extranonce2': '00000000', 'job_id': u'1db7' }
  log('TEST: Correct answer %r' % valid, LEVEL_DEBUG)



# CLI for cpu mining
if __name__ == '__main__':
  import argparse

  # Parse the command line
  parser = argparse.ArgumentParser(description="PyMiner is a Stratum CPU mining client. "
                                               "If you like this piece of software, please "
                                               "consider supporting its future development via "
                                               "donating to one of the addresses indicated in the "
                                               "README.md file")

  parser.add_argument('-o', '--url', help = 'stratum mining server url (eg: stratum+tcp://foobar.com:3333)')
  parser.add_argument('-u', '--user', dest = 'username', default = '', help = 'username for mining server', metavar = "USERNAME")
  parser.add_argument('-p', '--pass', dest = 'password', default = '', help = 'password for mining server', metavar = "PASSWORD")

  parser.add_argument('-O', '--userpass', help = 'username:password pair for mining server', metavar = "USERNAME:PASSWORD")

  parser.add_argument('-a', '--algo', default = ALGORITHM_SCRYPT, choices = ALGORITHMS, help = 'hashing algorithm to use for proof of work')

  parser.add_argument('-B', '--background', action ='store_true', help = 'run in the background as a daemon')

  parser.add_argument('-q', '--quiet', action ='store_true', help = 'suppress non-errors')
  parser.add_argument('-P', '--dump-protocol', dest = 'protocol', action ='store_true', help = 'show all JSON-RPC chatter')
  parser.add_argument('-d', '--debug', action ='store_true', help = 'show extra debug information')

  parser.add_argument('-v', '--version', action = 'version', version = '%s/%s' % (USER_AGENT, '.'.join(str(v) for v in VERSION)))

  options = parser.parse_args(sys.argv[1:])

  message = None

  # Get the username/password
  username = options.username
  password = options.password

  if options.userpass:
    if username or password:
      message = 'May not use -O/-userpass in conjunction with -u/--user or -p/--pass'
    else:
      try:
        (username, password) = options.userpass.split(':')
      except Exception, e:
        message = 'Could not parse username:password for -O/--userpass'

  # Was there an issue? Show the help screen and exit.
  if message:
    parser.print_help()
    print
    print message
    sys.exit(1)

  # Set the logging level
  if options.debug:DEBUG = True
  if options.protocol: DEBUG_PROTOCOL = True
  if options.quiet: QUIET = True

  if DEBUG:
    for library in SCRYPT_LIBRARIES:
      set_scrypt_library()
      test_subscription()

    # Set us to a faster library if available
    set_scrypt_library()
    if options.algo == ALGORITHM_SCRYPT:
      log('Using scrypt library %r' % SCRYPT_LIBRARY, LEVEL_DEBUG)

  # The want a daemon, give them a daemon
  if options.background:
    import os
    if os.fork() or os.fork(): sys.exit()

  # Heigh-ho, heigh-ho, it's off to work we go...
  if options.url:
    miner = Miner(options.url, username, password, algorithm = options.algo)
    miner.serve_forever()
