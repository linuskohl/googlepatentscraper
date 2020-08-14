*******************
googlepatentscraper
*******************

**Note:** This client is not affiliated with Google

Table of Contents
#################

* `Install <#install>`_
* `Usage <#usage>`_
* `License <#license>`_

Install
#######

Install with pip:

```sh
pip install googlepatentscraper
```

Usage
#####


Load document from google patents
*********************************


.. code-block:: python

    from googlepatentscraper.document import Document

    patent = Document("US8400417B2")
    pprint(patent.data)


License
#######


This code is distributed under the terms of the GPLv3  license.  Details can be found in the file
[LICENSE](LICENSE) in this repository.

Package Author
##############

Linus Kohl, <linus@munichresearch.com>

