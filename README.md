# aws_blueprint_ebs_wordpress_efs_rds

## Overview
Blueprint for Amazon Web Services (aws) to deploy the latest version of WordPress in a $5.56 (single instance) vs $25.50 (autoscaling) per month config that can be quickly toggled back and forth as needed via the ElasticBeanstalk interface in the aws console. The build process assumes this blueprint when building the deployable ElasticBeanstalk package.

Prices assume sites are running 24 hours a day for the entire month.

### Features

1. Permalinks > Custom Structure supported by default.
    * Apache mod_rewrite enabled by default (.htaccess included).

### Architecture

#### TODO
[RDS_EFS_DIAGRAM]

## Quick Start

### Building Deployable ElasticBeanstalk Packages
./build.py --site-name "[YOUR SITE NAME]"

Download wordpress, populate `keys.config` with new salts, 
and generate an easily configurable ElasticBeanstalk package for managing 
multiple Wordpress installs using a single rds, efs, and multiple Beanstalk 
environment configs.

## References

### AWS Monthly Cost Calculator
<https://calculator.s3.amazonaws.com/index.html>

#### ~$5.56/month (Single Instance)
##### ElasticBeanstalk Scaled Down to Single t2.nano Instance, Autoscaling Disabled
<https://calculator.s3.amazonaws.com/index.html#r=IAD&s=EC2&key=calc-0BA3DA2A-C7D3-464B-B8BD-7411E86BB1F3>

Great for new site development and experimentation with low traffic.

#### ~$25.50+/month (AutoScaling Enabled)
##### ElasticBeanstalk Scaled Down to single t2.nano, 1 ELB, and 15 GB/Month of outgoing data from elb, with 8GB gp2 EBS volume
<https://calculator.s3.amazonaws.com/index.html#key=calc-175BBB4C-AB76-4D58-B61E-DB22ED66B2CE&r=PDX>

Great for having a site that scales up to as many t2.nanos as are necessary to accommodate traffic. Add $4.76 per additional instance scaling up.