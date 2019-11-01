# Data Quality Tester (DQT) - Technical notes

* [Live site](http://dataqualitytester.publishwhatyoufund.org/)

* [Repository](https://github.com/pwyf/data-quality-tester)

* [Deploy scripts](https://github.com/OpenDataServices/opendataservices-deploy/blob/master/salt/pwyf-dqt.sls)

## 1. User Input

The user has 3 different options available for uploading their data. They can upload the file itself, copy the XML into a text entry, or provide a URL to the file.

Handled by: upload.html

## 2. Uploading the Data

After HTTP POST upload a SuppliedData object instance is created which is a SQLAlchemy model. 

This object contains the data, location on disk and various metadata items. It also creates a unique id (uuid) for this test run and triggers a Celery task for downloading the data if it is hosted remotely.

Handled by: views/uploader.py , models.py, (tasks.py download_task)

## 3. Processing the Data

The upload page redirects to the package overview page, which contains the unique id. The view function for this page starts a Celery task to run the tests on the values provided by looking up the unique id in the database.

Handled by: views/quality.py, overview.html

## 4. Updating the status of tests 

The quality overview view module renders the overview template which contains a JS XHR (ajax) which polls the status API endpoints every 2 seconds. The url for the endpoints to poll is stored in the data property of the HTML elements representing the tests. For example data-status-url="/task/42f0bca1-84fc-46fd-9740-e2299aabdc75"

This queries the Celery task of the id given and returns the status for all the tests in that group. 

Status results example:

```json
{
   "colour": "#222",
   "data": {
      "Allocation policy is present": {
         "failed": 0,
         "not-relevant": 3,
         "passed": 0

      },

      "Annual report is present": {
         "failed": 0,
         "not-relevant": 3,
         "passed": 0
      },
      "status": "SUCCESS"
   }
}
```

When this JSON document is returned it is rendered on the client side using Mustache(JS).

Handled by: tasks.py, views/quality.py, overview.html

## 5. Test Results

The original data file to be tested is stored to the media folder (as configured in config.py). This folder will also contain the test results and summary JSON file for each test group. The media folder is named with the unique id of the test run (a uuid).

The testing process is done with the [BDD_Tester tool](https://github.com/pwyf/bdd-tester) that uses the Index Indicator Definitions ([e.g. 2018](https://github.com/pwyf/2018-index-indicator-definitions)) repository for all cucumber/gherkin style feature files and step definitions. The repository is a submodule in the repository. 

The outputs from the tests are stored in CSV files alongside the original data file.

The package summary page retrieves the record from the database via the UUID, this record provides the file locations to the results CSVs. These files are used to generate the render context for the package, project attributes and test templates/pages.

Handled by: views/quality.py, overview.html

## 6. Clean up

There is a Flask command ‘flask flush-data’ which will delete Test results files from the media directory that are older than 7 days or all using --all.

This command can be run in a cron job.

Handled by: command.py

# Running

Options for running the Data Quality Tool

## Developer local install

[Installation instructions](https://github.com/pwyf/data-quality-tester/blob/develop/README.md)

Redis can be installed from your system’s package manager. Redis server version 4.0.9 is known to work.

## Developer install in Vagrant

[Vagrant Development](https://github.com/pwyf/data-quality-tester/tree/develop-with-vagrant/vagrant)

## Deploy to a virtual/cloud/dedicated server

Using SaltStack:

1. Git clone and install  [https://github.com/opendataservices/opendataservices-deploy](https://github.com/opendataservices/opendataservices-deploy)

2. Create ./pillar/private/pwyf_dqt_pillar.sls with an entry for secret_key : e.g. 
```yaml
  pwyf_dqt_private:
  # pwgen -n 50 -y
    secret_key: htohg1Za6doh[y6Enge!zeej8air6ew|oh^tuFigheex&ei^Y
```

3. Append an entry to ./salt-config/roster called pwyf-dqt-[something] : e.g.

```yaml
# Publish What You Fund (PWYF)
pwyf-dqt-test: 172.17.0.2
```

4. Update and install on the target server using salt-ssh e.g. salt-ssh -i --state-output=mixed 'pwyf-dqt-test' state.highstate

