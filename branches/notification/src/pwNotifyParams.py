import xml.dom.minidom as dom
import os.path


class PwytterNotifications(object):
    """Handle the Pwtytter Notifications in an XML file Notifications.xml
    """
    def __init__(self,api):
        self.api=api
        self.storage_notification_directory = "~/.pwytter/Notifications"
        self.storageNotifications = os.path.expanduser(self.storage_notification_directory)
        self._notificationFileName = os.path.join(self.storageNotifications,'notification.xml')
        self.values = {}
        self._resetDefaults()
        if not os.path.exists(self.storageNotifications):
            os.makedirs(self.storageNotifications)
            self.writeToXML()

    def _resetDefaults(self):
        self.Friends = self.api.GetFriends()
        for frnd in self.Friends :
            self.values[frnd.screen_name]='1'
        self.values['FilterString']=''

    def __getitem__(self, aKey):
        return self.values[aKey]

    def __setitem__(self, aKey, value):
        self.values[aKey] = value

    def readFromXML(self):
        self._resetDefaults()
        self._notifyDoc = dom.parse(self._notificationFileName).documentElement
        assert self._notifyDoc.tagName == 'notifications'
        for val in self.values.keys():
            try :
                node = self._notifyDoc.getElementsByTagName(val)
                self.values[val] = node[0].firstChild.data.strip()
            except Exception, e:
                print '!! Exception in process_node_string'+str(e)
                #self.values[val]=''
        print self.values

    def writeToXML(self):
        impl = dom.getDOMImplementation()
        self._notifyDoc = impl.createDocument(None, 'notifications', None)
        top_element = self._notifyDoc.documentElement
        for val in self.values.keys():
            Element = self._notifyDoc.createElement(val)
            Element.appendChild(self._notifyDoc.createTextNode(str(self.values[val])))
            top_element.appendChild(Element)
        f = open(self._notificationFileName, 'w')
        f.write(self._notifyDoc.toprettyxml())
        f.close()