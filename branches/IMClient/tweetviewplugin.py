# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtDesigner import QPyDesignerCustomWidgetPlugin
from tweetview import TweetView

"""Plugin for using TweetView in QtDesigner"""

class TweetViewPlugin(QPyDesignerCustomWidgetPlugin):
    """A modification of QTextBrowser to view tweets"""
    # The __init__() method is only used to set up the plugin and define its
    # initialized variable.
    def __init__(self, parent = None):
        QPyDesignerCustomWidgetPlugin.__init__(self)
        self.initialized = False

    # The initialize() and isInitialized() methods allow the plugin to set up
    # any required resources, ensuring that this can only happen once for each
    # plugin.
    def initialize(self, formEditor):
        if self.initialized:
            return
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    # This factory method creates new instances of our custom widget with the
    # appropriate parent.
    def createWidget(self, parent):
        return TweetView(parent)

    # This method returns the name of the custom widget class that is provided
    # by this plugin.
    def name(self):
        return "TweetView"

    # Returns the name of the group in Qt Designer's widget box that this
    # widget belongs to.
    def group(self):
        return "Pwytter"

    # Returns the icon used to represent the custom widget in Qt Designer's
    # widget box.
    def icon(self):
        return QIcon(_logo_pixmap)

    # Returns a short description of the custom widget for use in a tool tip.
    def toolTip(self):
        return "Can display messages and users"

    # Returns a short description of the custom widget for use in a "What's
    # This?" help message for the widget.
    def whatsThis(self):
        return "A widget for display messages and users in pwytter, allows theming."

    # Returns True if the custom widget acts as a container for other widgets;
    # otherwise returns False. Note that plugins for custom containers also
    # need to provide an implementation of the QDesignerContainerExtension
    # interface if they need to add custom editing support to Qt Designer.
    def isContainer(self):
        return False

    # Returns an XML description of a custom widget instance that describes
    # default values for its properties. Each custom widget created by this
    # plugin will be configured using this description.
    def domXml(self):
        return '<widget class="TweetView" name="tweetView" />\n'

    # Returns the module containing the custom widget class. It may include
    # a module path.
    def includeFile(self):
        return "tweetview"


# Define the image used for the icon.
"""_logo_32x32_xpm = [
    "32 32 118 2",
    "AB c #010101", "AD c #030303", "AE c #040404", "AH c #070707",
    "AI c #080808", "AJ c #090909", "AN c #0d0d0d", "AO c #0e0e0e",
    "AP c #0f0f0f", "AQ c #101010", "AR c #111111", "AS c #121212",
    "AT c #131313", "AU c #141414", "AV c #151515", "AX c #171717",
    "AY c #181818", "AZ c #191919", "BA c #1a1a1a", "BB c #1b1b1b",
    "BC c #1c1c1c", "BD c #1d1d1d", "BE c #1e1e1e", "BF c #1f1f1f",
    "BK c #242424", "BL c #252525", "BM c #262626", "BN c #272727",
    "BO c #282828", "BU c #2e2e2e", "BW c #303030", "BX c #313131",
    "BZ c #333333", "CF c #393939", "CI c #3c3c3c", "CK c #3e3e3e",
    "CL c #3f3f3f", "CM c #404040", "CN c #414141", "CO c #424242",
    "CP c #434343", "CR c #454545", "DG c #545454", "DH c #555555",
    "DI c #565656", "DJ c #575757", "DK c #585858", "DN c #5b5b5b",
    "DO c #5c5c5c", "DP c #5d5d5d", "DQ c #5e5e5e", "DR c #5f5f5f",
    "DS c #606060", "DT c #616161", "DU c #626262", "DY c #666666",
    "EA c #686868", "ED c #6b6b6b", "EE c #6c6c6c", "EI c #707070",
    "EL c #737373", "EQ c #787878", "ET c #7b7b7b", "EU c #7c7c7c",
    "FA c #828282", "FB c #838383", "FD c #858585", "FF c #878787",
    "FG c #888888", "FI c #8a8a8a", "FK c #8c8c8c", "FL c #8d8d8d",
    "FO c #909090", "FS c #949494", "FY c #9a9a9a", "FZ c #9b9b9b",
    "GB c #9d9d9d", "GC c #9e9e9e", "GF c #a1a1a1", "GH c #a3a3a3",
    "GR c #adadad", "GU c #b0b0b0", "GV c #b1b1b1", "GY c #b4b4b4",
    "GZ c #b5b5b5", "HB c #b7b7b7", "HC c #b8b8b8", "HE c #bababa",
    "HL c #c1c1c1", "HO c #c4c4c4", "HP c #c5c5c5", "HU c #cacaca",
    "HY c #cecece", "HZ c #cfcfcf", "IB c #d1d1d1", "IC c #d2d2d2",
    "ID c #d3d3d3", "IE c #d4d4d4", "IG c #d6d6d6", "IH c #d7d7d7",
    "II c #d8d8d8", "IJ c #d9d9d9", "IK c #dadada", "IL c #dbdbdb",
    "IM c #dcdcdc", "IO c #dedede", "IS c #e2e2e2", "JB c #ebebeb",
    "JC c #ececec", "JD c #ededed", "JE c #eeeeee", "JF c #efefef",
    "JH c #f1f1f1", "JP c #f9f9f9", "JR c #fbfbfb", "JT c #fdfdfd",
    "JU c #fefefe", "JV c #ffffff",
    "JVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJVJVJVJVJVIMFDCMBLBLCNFFIOJVJVJVJVJVJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJVJVJDDOANABADAJAZAZAJADABAODPJFJVJVJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJRDUADBEDSBDHEJVJVJVJVHCBCDTBDADDYJTJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVIKAVARGZHZBEILJVJVJVJVJVJVIIBFICGYAQAYIOJVJVJVJVJVJV",
    "JVJVJVJVJVHUAHCRJRJRBUHEJVJVJVJVJVJVJVJVHBBXJRJRCOAIHYJVJVJVJVJV",
    "JVJVJVJVIKAHDUJVJVFYDKJVJVJVJVJVJVJVJVJVJVDIGBJVJVDQAIIOJVJVJVJV",
    "JVJVJVJRAVCRJVJVJTBLIIJBHLGFFKFAFAFKGFHLJCIEBNJTJVJVCMAYJTJVJVJV",
    "JVJVJVDUARJRJVJTFKBBBKAOCFDOEDEQEUELDQCLAUBLAZFOJTJVJPAPEAJVJVJV",
    "JVJVJDADGZJRFYBKBADGIJJUJVJVJVJVJVJVJVJVJUILDIBBBMFZJRGUADJFJVJV",
    "JVJVDOBEHZBUDHHZBKIMJVJVJVJVJVJVJVJVJVJVJVJVIJBMIGDJBWIBBCDRJVJV",
    "JVJVANDSBDGVJVJBAUJUJVJVJVJVJVJVJVJVJVJVJVJVJUATJEJVHCBEDQAPJVJV",
    "JVIMABAZIDJVJVHLCLJVJVJVJVJVJVJVJVJVJVJVJVJVJVCIHOJVJVIJBCABISJV",
    "JVFDADGVJVJVJVGFDQJVJVJVJVJVJVJVJVJVJVJVJVJVJVDOGHJVJVJVHBADFGJV",
    "JVCMAIJUJVJVJVFKELJVJVJVJVJVJVJVJVJVJVJVJVJVJVEIFLJVJVJVJVAICPJV",
    "JVBLAXJVJVJVJVFAEUJVJVJVJVJVJVJVJVJVJVJVJVJVJVETFBJVJVJVJVAZBMJV",
    "JVBLAZJVJVJVJVFAEUJVJVJVJVJVJVJVJVJVJVJVJVJVJVETFBJVJVJVJVAZBMJV",
    "JVCNAJJVJVJVJVFKELJVJVJVJVJVJVJVJVJVJVJVJVJVJVEIFLJVJVJVJUAICPJV",
    "JVFFADHCJVJVJVGFDQJVJVJVJVJVJVJVJVJVJVJVJVJVJVDNGHJVJVJVGZADFIJV",
    "JVIOABBCIIJVJVHLCLJVJVJVJVJVJVJVJVJVJVJVJVJVJVCIHPJVJVIHBCABISJV",
    "JVJVAODTBFHBJVJCAUJUJVJVJVJVJVJVJVJVJVJVJVJVJUASJEJVGZBFDSAPJVJV",
    "JVJVDPBDICBXDIIEBLILJVJVJVJVJVJVJVJVJVJVJVJVIJBNICDGBZIEBBDTJVJV",
    "JVJVJFADGYJRGBBNAZDIIJJUJVJVJVJVJVJVJVJVJUIJDGBABOGCJRGRAEJHJVJV",
    "JVJVJVDYAQJRJVJTFOBBBMATCIDOEIETETEIDNCIATBNBAFSJTJVJPAOEEJVJVJV",
    "JVJVJVJTAYCOJVJVJTBMIGJEHOGHFLFBFBFLGHHPJEICBOJTJVJVCKBAJTJVJVJV",
    "JVJVJVJVIOAIDQJVJVFZDJJVJVJVJVJVJVJVJVJVJVDGGCJVJVDOAIISJVJVJVJV",
    "JVJVJVJVJVHYAICNJRJRBWHCJVJVJVJVJVJVJVJVGZBZJRJPCKAIHZJVJVJVJVJV",
    "JVJVJVJVJVJVIOAYAPGUIBBEIJJVJVJVJVJVJVIHBFIEGRAOBAISJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJTEAADBCDQBCHBJVJVJVJUGZBCDSBBAEEEJTJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJVJVJFDRAPABADAIAZAZAIADABAPDTJHJVJVJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJVJVJVJVJVISFGCPBMBMCPFIISJVJVJVJVJVJVJVJVJVJVJVJV",
    "JVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJVJV"]
    """
_logo_32x32_xpm = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00\tpHYs\x00\x00\r\xd7\x00\x00\r\xd7\x01B(\x9bx\x00\x00\x00\x19tEXtSoftware\x00www.inkscape.org\x9b\xee<\x1a\x00\x00\x06\xafIDATX\x85\xad\x97{lS\xd7\x1d\xc7?\xf7\xda\xf1#vb\'8\x81<\x16p0!\x0f\x1a\x02\xce(mY\xd3\x8dvl<\x0b[5\xc6F\xb7N\xabF\xabJ\xdb$\xd8\xd2NS\xc7:&:\x18\x95\xb6\xaa\xaa\xfa\xdc\x98\xd6\x8d>V\x8a\x1a\xb4\xa7`P\x9e\xb1\xe9B\x05I\x08\xc4\xc0 &$\xd8\xe4\xe1\xf8u\xef=\xfb\xc3qlGI0\x1d?\xe9H\xf7\xfc\xce\xf9\xfd\xbe\xdf\xf3{\x1c\xfbHB\x08\xa6\x92F/6\xa0atD\x80\xff\x00\x9fx\xdc\x8cLi\x98\xa5H\x13\x11h\xf4\xa2\x036\x03\xdf\x03\x9c\x13\xd8i@\'\xb0\xcd\xe3\xe6\x8fw\x94@\xa3\x97\xb9\xc0\xef\x80\xc5Y\xfax\x07\xd8\xe4q\x13\xf8\xbf\t4z\xd9\x08\xbc\x02\x98\x00\x1c9\xb0\xb4\x00\xaas\x13#.\xa0#\x04\xed#\xf0\xb7\x00\x8chc\xa6~\xe0+\x1e7\xc7>5\x81F/\xb5\xc0)\xc0\x08\t\xe0\x9fT@\xbe~b\xc3+Q\xf8\xa9\x0f>\t\xa5T\xc0<\x8f\x9b\x81\xdb! \x8f\x82\xeb\x81\xddI\xf0\xcd\x9f\x81\xe7+\'\x07\x07(7\xc2ksa\xad#\xa5\x02~s;\xe0c\x04\x80f\xc0\r\x89\x93\xaf/\xce\xdc\xa4\x01\x87\x07\xe0\xe4`\xa6^\'\xc1\x96\n\x98m\x1eS=\xda\xe8e\xcd\xed\x10H\x9e\xf1;\x00\xd3r\xe0\x99\x8a\xd4\xe2\x88\x06\x7f\xee\x85\xf7\xfb\xc1\x1fK\xe8*\xcd\xb0\xbe\x08\x1ev\x80,\x81A\x82\xe7\x9c\xf0\xad\xf6D\x8d\x90\xe8\x9c\x0f\xb2% \x8f\xf6\xb9\x13`Y!\xd8\xd2\xc2\xfen\x1f\xbc\xd4\x93\x02\x07\xe8\x0e\xc3//\xc3\x91\xb4hT\x99\xe1.\xeb\xd8tA\xb6\xe0\x90HACrR\x9d\n%\x9a\x80w\xae\x8fM\x07\x80\xad\xc0N \x06\xf0vj\r\x80\xba\xdc\xb1\xcf\x19\x8d^\xa6\xdf\x0e\x81\xf9\xc9IU\xca\t\xc7\x063N\xfek\x8f\x9b\x9fy\xdcl\x01\xde\x058>\x08=i\x91\xa9\xb1d\xf8m K\x91\x81\xc2\xe4\xa4 -\xfc\x01%c_K\xda\xf74\x00I\x02\xb3\x9cR\xaa\x99\xf7Y$[\x02S4Z\x86\xacl\xf4\xd2\x08\xac\x03\x96\x01<`\xcf$\xdc\x99\xf9\xcb\xd0v\xa7\tl\x1d\xafX_\x94\x86\xd6\xe9\xe7`\xdbM\x98U\x05:\xddE\x8f\x9b\x9bw\x9a\x00\x009\x12|\xde\x0ek\x8b`a\x1e\xec=x\x86\x9d\xbb\x0fc\xb4\x98\xc9\xb7Z\xc8k;G\xf0\xde\xc5\xe7\xc8\xbe\x06\'\'\xd0d\x83\xb7j2u\xd3\r\x99mz\xaa\xbd\x87\x1b\xc1\x10\x0f\xd5Wr\xe0X;5sfR\xe69\xba\xd0\xf5\xca\x85\xc7\xcf\x7f\xb0\xf9\xd5\xe4>\xe7\x8a\xed\xf5\xb2N^\xad\xa9\xdaa_K\xf3\xbf\xb3"\x90\xaf\x9f\xfa*\x06\xe8\xb8\xd4\x87!\xd7D\xffp\x9co?\xd2\xc4{\xfbO \xe9\r\x8e/7\xd5\xbf\xd0\xb0\xe1\xb7\x0f\x0e\xf4\xde|\xcc>\xdd\xf6amU\xd9g]\xb3fX\xda\xcf_\x8d\xccyx\xe7[]{7\x7f7\xe9C\x9e\n`*i\x1d\x82\xae\x1ba\x96?0\x9f\xb2\xd2b\xfaGT\xbe\xbe\xf6~\xca\x1c\x16\x0e\xb5vY\xea\xaa*\x1e\x996\xa3``\xe9\x92\xbb\xee\xaf\xaa\x9dc\x8d\xc8&\xa9~~\xb5\xb9fv\xc9z\xd7\xea\x1d\x8f\xdd2\x027\xe2\xd0\x19\xce\xd4\xf5\xc7\xa0#\x9c\xa8\xf8\xd3\xc3 \x96/\xe3\xc4\x81\x03|\xa9i\x01C\x11\x85`(\xce\xa2E\xf3\xa8q\x059z\xea\x9c\xb4\xe1\xabM\xfa\x9e`\x18-\xaeb\xc8\xd1Q:-\x17\xdb\xc2*KG\xf7\xb5-\xc0\x9bS\x12\xf0\x0e\xc13\xbe\xa9\xa3\xa0\xaf(W{\xf3\n\x8e\xb7\x9f=\xbf`n\x8d+W\x03\x84\x90\xb0\xd8\x0bX\xb9\xec\x1e\xfa\x06\xc2\xc8\x92\x84$I,\xa9)fqu1\xef\x1f\xf1\x91o5\x15;Wl7\xf9Z\x9a#\x9f&\x05\x1ap\x0e\xd8\x03\xdc{f\xdb\xca%\'\xda|\xad\xf1\xd0\xa0"#!\x00U\x08\x06B\xb1\x0c\xa3\xc2<#\x8a*\xe8\xee\x1d\xe2swW\xdb\xa6;l\xd7\\kv\xec\xcd\xb6\r\x7f<\n\xda\x0b\x9c\xf6\xb8\t\xa5/\x86\xc3\xd1/\xec\xf9\xf0\xe4\xb5\xe6\xa7\xd6\x14]\xec\x1dF\x13\x02U\xd3\xd04\rM\x084!8x\xda\xcf\xd1\xb3\xbd\x04\x87"\xcc\xb0\xea\xa4p4\x16\xd1TmW\xb6\x04\x0ey\xdc\x1c\x9fl\xd1h4\xbc<\xaf\xaa,\xd7\x1f\x18!\x1aWA\x08TM\xa0\xa8\x1a\xaa*\xd04A\xdf`\x84x\\A\x92\xa0\xed\x8c/<8\x14\xae\xf5\xb54\x07n\x99\x02\xe5\xaa\x9f\xd0\xfe\x7f\xd4O\xb6^\xbdn\xd7\xbe\xc5\r\x95\xdf\xac\xaesY\xfan\x8e\x10\x8b+\xc4\x14\x95\xb8\xa2\x12W4\x14U\x1d%\xa2\xa1j\x02\xb3A\xcf\xf0H4\xeaki\x0e@\x167\xa1d0\x10;\xf9\xf1Ks\xd7\x9e~:\xae(\xdb\x84&v\xfbZ\x9ac\xae\xd5;\x1e\xb7\xe4\x1a~\xf1\xe0\x92:\x9b\xd9f7\x06\x86"c\x05\x07\x89S\xab\x9a@U5\x14U\xa3\xc4nd\xa6\xc3H\xaeQ\x8f\xf7\xa4\x12M\xfa\xbf%\x01]\xd14\x0c\xf55?*\x0f\xf6m-\x9dQ\xf0\xe2\x7f\xfd\xc1\x17\x96>\xf9\x06\x8b\x1a*\xf5s\xe6T\x98\xae\x04B\xc4BQdYF\x96%\x12\xf0 \x84@\x02\xeag\xd9\xb8\xa7\xaa\x90R{\x0e\xb1X\x8c\xae+\x03\xe8e>\xca\x9a\x00\x80e\xdd\xaa\xa3\xdd[w<k0\xe6\xfc\xbc\xa6n\xb6\xb5o0\x82\x02t\xf5\x0c\xa0\xd3I\xe8d\x81,k\xc8\x92\x04\xa3\x14\xac\xa6\x1c6-sQR`$\x1e\x8f\xa3(\n:\x9d\x8e\xdd\xfbOGzo\x0coL\xfa\x96!\xf5\xa0h\x1dJ\x81\xa6\x7f\x03\x81\x0b\xfb\xb6\xec\xea\xec\xbe\xf6\x87\x0b\xe7.\x86\xec\x16\x03qEK\xe49\xae\x12\xcb\x18\nV\xa3\x8e\'\xbe8\x0b\x87U&\x1a\x8d\x8e\x118v\xa6Gt\\\xba\xf1W_K\xf3X\x8fJn\x8fp\x90\xf8Oo,7\xc2\xa6R\xe8\x8f\xc3\xcb=\x10I<<\x8ez\xdc\xdc\x974\x98\xbd\xeaW\xdfp\x14Z_\xbc\xef\xeeZ\xfb\xa5@\x04!\x04:YF\x92$$\tl\xe6\x1c\xbe\xbf\xdc\x89\xdd\x92\x03\xa3\xa9\x10B\xd0q9\xc8so\x1c9{\xe8\xf5\'\xea\xd2O&\t!h\xf4\xf2{\xe0\xd1I2\xb0\xc1\xe3\xe6O\xe9\n\xe7\x8a\xed%&\x93\xe1\xf0\xfc\xda\x99\xe5\xc5%\x0e\xa3?0B\\\x15H\x92DS\xb5\x9dU\xee\xe2\xd1b\x04\xbd>\x87}\x1f\x9d\x17o\xff\xab\xfd\xfc\xa1\xd7\x9f\xac\x1a\xef<Y\x03\xcf\x92\xa8\x9d\xaf1\xfa,#q\xe9\xbc\x06\xfce\xbc\x91\xaf\xa5\xd9\x0f\xb8*W>\xff\x94\xb9\xe3\xf2\x0fJ\x8al\xc5\xceY%yyV3\x85\xf9&t:\x1d\xfe\xfe\x10\x1fw]\x17\xffl\xbd\x14\xbep5\xf8t\xdb\x9e\x1fN\xf8h\x19\xff6,\x046\x02\xd7\x81\xf7<nb\x13\x19\x8d\x17\xe7\x8a\xedNY\'o\x91$\xa9\xc6j6L\xb7[\x8d\xa6\xc1P\xb458\x18~\x13\xf8\xbb\xaf\xa5Y\x9b\xcc\xf6\x7f}\xd8\xaex\x9c9\xe9\xb7\x00\x00\x00\x00IEND\xaeB`\x82'

_logo_pixmap = QPixmap(_logo_32x32_xpm)
