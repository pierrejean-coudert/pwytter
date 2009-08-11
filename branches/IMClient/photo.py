import base64
import os
import sha
import xmpp

PHOTO_DIR = "./photos/"

PHOTO_TYPES = {
    'image/png': '.png',
    'image/jpeg': '.jpeg',
    'image/gif': '.gif',
    'image/bmp': '.bmp',
    'image/jpg':'.jpg',
	}

def append_directory(filename):
    return os.path.join(PHOTO_DIR, filename)

def register_handler(session):
    session.RegisterHandler('presence', photo_update_handler)

def photo_update_handler(session, stanza):
    JID = stanza['from'].getStripped()
    vupdate = stanza.getTag('x', namespace='vcard-temp:x:update')
    if not vupdate:
        return
    photo = vupdate.getTag('photo')
    if not photo:
        return
    try :
    	photo = photo.getData()
    except Exception , e :
	pass 	
    if not photo:
        return
    #request the photo only if we don't have it already
    if not get_photo(photo):
        try:
		request_vcard(session, JID)
	except Exception,e :
		pass

def get_photo(photo_hash):
    for ext in PHOTO_TYPES.values():
        filepath = append_directory(photo_hash + ext)
        if os.path.exists(filepath):
            return filepath

def request_vcard(session, JID):
    n = xmpp.Node('vCard', attrs={'xmlns': xmpp.NS_VCARD})
    iq = xmpp.Protocol('iq', JID, 'get', payload=[n])
    return session.SendAndCallForResponse(iq, recieve_vcard)

def recieve_vcard(session, stanza):
    photo = stanza.getTag('vCard').getTag('PHOTO')
    if not photo:
        return
    photo_type = photo.getTag('TYPE').getData()
    photo_bin = photo.getTag('BINVAL').getData()
    photo_bin = base64.b64decode(photo_bin)
    ext = PHOTO_TYPES[photo_type]
    photo_hash = sha.new()
    photo_hash.update(photo_bin)
    photo_hash = photo_hash.hexdigest()
    #name=stanza['from'].getStripped()
    filename = append_directory(photo_hash + ext)
    file(filename, 'wb').write(photo_bin)

