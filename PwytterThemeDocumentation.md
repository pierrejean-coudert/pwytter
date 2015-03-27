This document outlines how themes for Pwytter should be written and packaged. This document is still a draft and shall be subject to change. This document is **only** relevant to the backend-split branch in SVN, once this branch is released this document should become stable. Note that this document serves as documentation and is **not** a tutorial for writing Pwytter themes.

# Introduction #
Pwytter can be customized using Qt stylesheets and the TweetView can be customized using HTML, CSS, etc. Each theme resides in it's own directory, this is called the theme directory. Any sub-directory in the "theme" of the pwytter is a theme directory. The name of the theme directory is the name of the theme, this name may only consist of alphanumeric characters. Note that the name of the theme must be unique, and will not be presented to the user for other purposes that error messages.

# Meta information #
In each theme directory there must be a file called `info.yaml` and `preview.png`. The `preview.png` is a preview of the theme in PNG format, this image will be presented when the user selects a theme. The file `info.yaml` contains meta-data about the theme in YAML 1.1 format, please refer to [yaml.org](http://yaml.org/spec/1.1/) for a specification of this format. The file contains following keys:

| **Key**	    | **Description** |
|:------------|:----------------|
| `Title`        | The title of the theme, this will be presented to the user instead if the theme name. |
| `Authors`      | A dictionary of authors, author name as key and e-mail as value. |
| `Website`      | Website for the theme, a link that will be available to the user. |
| `Version`      | Version of the theme, as string, add two dots or use quotation to ensure it's not interpreted as a float. |
| `Requires`     | Required API version that this theme is written for, as string, add two dots or use quotation to ensure it's not interpreted as a float. |
| `Description`  | Text that describes this theme, this text will be presented to the user when selecting theme. |
| `QtStyles` | An optional list of QStyles to be used with the theme. The first QStyle will be used if it is available, otherwise the next QStyle on the list will be used. See [Qt documentation](http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qstylefactory.html#create) for information on available QStyles. If no style is provided system default QStyle is used. |

**Note:** info.yaml must be UTF-8 encoded.

## Versioning ##
The meta information contains two different version numbers, the theme version (`Version`) and the API version (`Requires`). These version numbers must consist of three numbers: major.minor.maintenance. The theme version is currently not used for anything, and mainly mean to assist users. The API version denotes the version of this documentation that the theme is written for. This version number is currently 0.1.0. The major version is incremented whenever backwards compatibility is broken. The minor version is incremented when a new feature is exposed, which themes need to expose to the user. The maintenance version is incremented whenever a small insignificant feature is added, for instance a convenient variable, that exposes otherwise information which could be obtained otherwise using the old API.

# Templates #
The widget in Pwytter is called TweetView, this is the widget that displays tweets and users. This widget is based on WebKit and it's content is generated using templates. A theme must contain such templates. These templates can be written using any technology that runs in WebKit such as HTML, CSS, Javascript, images, Javascript etc. These templates must always be UTF-8 encoded.

Pwytter uses [Tinpy](http://sourceforge.net/projects/tinpy/), a minimalistic python template engine, to render the templates. Tinpy supports only a very limited set of features and complex expressions are not possible, should you require such then consider implementing them using Javascript. To insert a variable write `[% var VARIABLE %]` where `VARIABLE` is the variable you wish to insert, this can also be used to access dictionary variable such as `[% var Message['Text'] %]`. To start a loop over a list of variables write `[% for Message in Message %]` and end the loop using `[% done %]`. A template can also contain conditional statements if `[%if Message['CanReply']%]` and ended with `[% endif %]`, not if statements can being contained within eachother, but they cannot be negated or combined to one expression.

All `http://` links will be opened in an external web browser, it is possible fetch resources, such as images, from the Internet in a template, however, such behavior is strongly discouraged.URIs that starts with `pwytter://` can point to different views and resources in the theme directory, most important views shown below:

  * `pwytter://view/timeline/<account>/<page>`
  * `pwytter://view/replies/<account>/<page>`
  * `pwytter://view/direct messages/<account>/<page>`
  * `pwytter://view/outbox/<account>/<page>`
  * `pwytter://view/followers/<account>/<page>`
  * `pwytter://view/friends/<account>/<page>`

Where `<account>` is the string representation of an account, and `<page>` is page number starting from 0. Themes does not need to know about these, and shouldn't use them for anything, as they may change in the future. However, an interesting view that themes might want to link to in some cases is the detailed user view:

  * `pwytter://view/user/<service>/<username>`

This view displays the detailed user template with the user specified by `<service>` string and `<username>` on the given service. When displaying a list of users or a list messages themes may prefer not to display all details of a user and instead choose to link to this detailed view.

A URI for the image of user can be seen below, where `<image-id>` is unique image identifer, you need not know about this URI as a variable contains the entire URI and not just the image identifier. Nevertheless, the URI is documented here for completeness, but themes should not rely on this URI.

  * `pwytter://image/cache/<image-id>`


If a theme wish to use external stylesheets or images these can, as previously mentioned, be loaded from the Internet, nevertheless, such behavior is strong discouraged as it breaks the theme when working offline. To solve this issue resources can also be loaded from inside the theme directory, using the following URI:

  * `pwytter://theme/<path-relative-theme-dir>`

Where `<path-relative-theme-dir>` is a path relative to the theme directory. Include an image called `pic.png` from the `/images/` sub-directory of the theme directory use `pwytter://theme/images/pic.png`. There are currently no restrictions on how resources can be stored in the theme directory, however, it is strongly recommended that images are stored in an `/images/` sub-directory. It is also recommended that Javascript, CSS and other resources are stored in a `/resources/` sub-directory of the theme directory.

## Messages template ##
When TweetView needs to display a list of messages the template in `Message.tpl` is used, this template must be present in the theme directory of a theme. The following variables are available to this template.

| **Variable**   | **Description**                        |
|:---------------|:---------------------------------------|
| `HasNextPage`  | True, if a next page exists.         |
| `HasPrevPage`  | True, if a previous page exists.     |
| `NextPage`     | URI of next page.                    |
| `PrevPage`     | URI of previous page.                |
| `Text`         | Translated text dictionary           |
| `Messages`     | List of message dictionaries         |

The template can use the following Javascript functions to make Pwytter perform an action:
| **Function**                   | **Description**                                                |
|:-------------------------------|:---------------------------------------------------------------|
| `window.pwytter.reply(<Id>)`   | Write a reply in reply to a message.                         |
| `window.pwytter.direct(<Id>)`  | Write a direct message in reply to a message.                |
| `window.pwytter.delete(<Id>)`  | Delete message, only possible for messages in the outbox.    |

Where `<Id>` is a message identifier, these identifiers are only assigned to message dictionaries in the `Messages` variable, and not to user dictionaries or message dictionaries on message dictionaries contained in the `Message` variable.

### Message dictionary ###
A message dictionary `Message` has the following fields:

| **Field** | **Description** |
|:----------|:----------------|
| `Message["Text"]` | Message text |
| `Message["User"]` | User dictionary for the user who posted this message. |
| `Message["Service"]` | Service this message was posted on. |
| `Message["Created"]` | Date and time for when this message was posted. |
| `Message["IsReply"]` | True, if this a reply. |
| `Message["ReplyAt"]` | User dictionary for the user this message is posted at/to, if this message is a reply. |
| `Message["IsDirectMessage"]` | True, if this a direct message. |
| `Message["DirectMessageAt"]` | User dictionary for the user this message is a direct message at/to, if this message is a direct message. |
| `Message["IsInReplyTo"]` | True, if this message is in reply to another message, may occur if the message is a reply or a direct message. |
| `Message["InReplyTo"]` | Message dictionary of the message this message is in reply to, if such message exists. |
| `Message["CanReply"]` | True, if a reply to this message is possible. |
| `Message["CanSendDirectMessage"]` | True, if a direct message in reply to this message is possible. |
| `Message["CanDelete"]` | True, if this message can be deleted, only possible for message in outbox. |
| `Message["Id"]` | Identifier of this message, used for certain Javascript functions. This identifier is page specific, not unique and only assigned to message dictionaries in the `Messages` variable of the messages template. |

### User dictionary ###
A user dictionary `User` has the following fields:

| **Field** | **Description** |
|:----------|:----------------|
| `User["Name"]` | Human readable name of the user. |
| `User["Username"]` | The user username, this combined with the service is unique. |
| `User["Service"]` | The service this user exists on, e.g. "twitter". |
| `User["Image"]` | URI to the users image. |
| `User["Description"]` | Description of the user. |
| `User["Location"]` | The location of the user. |
| `User["Url"]` | URL to the users website. |
| `User["IsFriend"]` | True, if the user is a friend. |
| `User["IsFollower"]` | True, if the user is a follower. |
| `User["CanReply"]` | True, if some account can reply to this user. |
| `User["CanSendDirectMessage"]` | True, if some account can send a direct message to this user. |
| `User["Id"]` | Identifier of this user, used for certain Javascript functions. This identifier is page specific, not unique and only assigned to user dictionaries in the `Users` variable of the user template, and to the "User" variable of the detailed user template. |

### Translated text dictionary ###
A dictionary with text string that are translated to the users language is also available to template write. This dictionary always has the identifier `Text` and it have the following fields:

| **Field** | **English translation** |
|:----------|:------------------------|
| `Text["Reply"]` | Reply |
| `Text["Retweet"]` | Retweet |
| `Text["Direct_message"]` | Direct message |
| `Text["Delete_message"]` | Delete message |
| `Text["Prev_page"]` | Prev page |
| `Text["Next_page"]` | Next page |
| `Text["Go_to_previous_page"]` | Go to previous page |
| `Text["Go_to_next_page"]` | Go to next page |
| `Text["<user>_on_<service>"]` | on |
| `Text["Description"]` | Description |
| `Text["On_<date>"]` | On |

## Users template ##
When TweetView needs to display a list of users the template in `Users.tpl` is used, this template must be present in the theme directory of a theme. The following variables are available to this template.

| **Variable**   | **Description**                        |
|:---------------|:---------------------------------------|
| `HasNextPage`  | True, if a next page exists.         |
| `HasPrevPage`  | True, if a previous page exists.     |
| `NextPage`     | URI of next page.                    |
| `PrevPage`     | URI of previous page.                |
| `Text`         | Translated text dictionary           |
| `Users`        | List of user dictionaries, see previous section for a documentation of user dictionaries. |

The template can use the following Javascript functions to make Pwytter perform an action:
| **Function**                   | **Description**                                                |
|:-------------------------------|:---------------------------------------------------------------|
| `window.pwytter.reply(<Id>)`   | Write a reply to a user.                                     |
| `window.pwytter.direct(<Id>)`  | Write a direct message to a user.                            |

Where `<Id>` is a user identifier, these identifiers are only assigned to user dictionaries in the `Users` variable.

## Detailed user template ##
When TweetView needs to display detailed information on one user the template in "Users.tpl" is used, this template must be present in the theme directory of a theme. The following variables are available to this template.

| **Variable**   | **Description**                                                                    |
|:---------------|:-----------------------------------------------------------------------------------|
| `Text`         | Translated text dictionary           |
| `User`         | User dictionary, see previous section for a documentation of user dictionaries.  |

The template can use the following Javascript functions to make Pwytter perform an action:
| **Function**                   | **Description**                                                |
|:-------------------------------|:---------------------------------------------------------------|
| `window.pwytter.reply(<Id>)`   | Write a reply to this user.                                  |
| `window.pwytter.direct(<Id>)`  | Write a direct message to this user.                         |

Where `<Id>` is a user identifier, this identifier is only assigned to user dictionary in the `User` variable.

# Qt stylesheets #
Pwytter can also be customized using Qt stylesheets, please note that this might break some native style engines such as GtkStyle for Qt. Note that these stylesheets should not rely on the object names of the Qt widgets. The Qt style is application wide and store in `application.qss` in the theme directory, this file is optional. Read more about Qt stylesheets in the [Qt documentation](http://doc.trolltech.com/4.5/stylesheet-reference.html).

# Theme packaging #
No packaging scheme or distribution channel implemented yet.