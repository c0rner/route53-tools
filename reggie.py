#!/usr/bin/env python

import argparse
import boto3
import json

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

if args['contacts'] is not None:
    contacts = read_json_contacts(args['contacts'])

domains = get_registered_domains(client)
print("Found {} registered domains in account".format(len(domains)))
#print(dir(client.exceptions))
exit()
try:
    result = register_domain(client, Domain=args['domain'], Contacts=contacts)
    print(result)
except client.exceptions.DomainLimitExceeded as e:
    print(e)
except Exception as e:
    print(e)
