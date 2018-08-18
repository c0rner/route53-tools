#!/usr/bin/env python

import argparse
import boto3
import json
from time import sleep

# The Route53 endpoint is located in us-east-1 as documented
# here https://docs.aws.amazon.com/general/latest/gr/rande.html
R53REGION='us-east-1'


def get_registered_domains(client):
    domains = []
    paginator = client.get_paginator('list_domains')
    for page in paginator.paginate(MaxItems=25):
        domains.extend(page['Domains'])
    return domains

    result = {}
    reply = client.list_domains(MaxItems=10)
    return reply['Domains']
    for item in reply['Domains']:
        print(".")
        name = item['DomainName']
        info = client.get_domain_detail(DomainName=name)
        result[name] = info
    return result

def get_domain_contacts(client, Domain=None):
    result = {}
    reply = client.get_domain_detail(DomainName=Domain)
    result['RegistrantContact'] = reply['RegistrantContact']
    result['AdminContact'] = reply['AdminContact']
    result['TechContact'] = reply['TechContact']
    return result

def register_domain(client, Domain=None, Contacts=None):
    result = client.register_domain(DomainName=Domain, DurationInYears=1,
            AdminContact=Contacts['AdminContact'],
            TechContact=Contacts['TechContact'],
            RegistrantContact=Contacts['RegistrantContact']
            )
    return result

def read_json_contacts(path):
    with open(path, 'r') as conf:
        return json.load(conf)

def read_domain_list(path):
    result = []
    # TODO This function should validate the domains
    with open(path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            result.append(line.strip())
    return result


parser = argparse.ArgumentParser(description='Reggie - The AWS domain registrator')
parser.add_argument('domainlist', type=str, nargs='?', help='File with list of domains')
parser.add_argument('-p', '--profile', type=str, metavar='AWS profile', required=True, help='AWS profile')
parser.add_argument('-c', '--contacts', type=str, metavar='jsonfile', help='Read contacts from json file')
parser.add_argument('--contacts-out', type=str, metavar='domain', help='Output contacts from existing domain')

args = vars(parser.parse_args())
if args['profile'] is None:
    parser.print_help()
    exit()

session = boto3.session.Session(profile_name=args['profile'], region_name=R53REGION)
client = session.client('route53domains')

if args['contacts_out'] is not None:
    info = get_domain_contacts(client, args['contacts_out'])
    print(json.dumps(info, indent=2))
    exit()

if args['contacts'] is None:
    print("Contacts JSON required!")
    exit()

if args['domainlist'] is None:
    parser.print_help()
    exit()

contacts = read_json_contacts(args['contacts'])
domains = read_domain_list(args['domainlist'])
#registered = get_registered_domains(client)
#print("There are {} registered domains in account".format(len(registered)))
#print(dir(client.exceptions))

for domain in domains:
    try:
        result = {}
        result = register_domain(client, Domain=domain, Contacts=contacts)
        print("Domain: '{}'".format(domain))
        print(result)
        if "ResponseMetadata" in result:
            sleep(result['ResponseMetadata']['RetryAttempts'])
    except (client.exceptions.DomainLimitExceeded,
            client.exceptions.OperationLimitExceeded) as e:
        print("{}\n\nAborting! Contact AWS support and request a limit increase.".format(e))
        exit(1)
    except (client.exceptions.ClientError) as e:
        print(e)
        exit()
    except Exception as e:
        print("Unhandled exception: {}".format(e))
        exit(-1)


#botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the RegisterDomain operation (reached max retries: 4): Rate exceeded
