"""Generating CloudFormation template."""
from ipaddress import ip_network

from ipify import get_ip

from troposphere import (
    Base64,
    ec2,
    GetAtt,
    Join,
    Output,
    Parameter,
    Ref,
    Template,
    Tags,
)

ApplicationName = "helloworld"
ApplicationPort = "3000"

GithubAccount = "JingPSE"
GithubAnsibleURL = "https://github.com/JingPSE/ansible".format(GithubAccount)

AnsiblePullCmd = \
    "sudo /usr/local/bin/ansible-pull -U {} {}.yml -i localhost".format(
        GithubAnsibleURL,
        ApplicationName
    )

PublicCidrIp = str(ip_network(get_ip()))

PoCTags=[{'Key':'costcenter','Value':'1223'},{'Key':'workorder','Value':'92008998'}]   

t = Template()

t.add_description("Effective DevOps in AWS: HelloWorld web application - Jing")

t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

t.add_resource(ec2.SecurityGroup(
    "SecurityGroup",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp=PublicCidrIp,
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ],
    Tags=PoCTags,
))

ud = Base64(Join('\n', [
    "#!/bin/bash",
    "sudo yum -y update",
    "sudo yum -y install java-1.8.0",
    "sudo yum -y remove java-1.7.0-openjdk",
    "curl --silent --location https://rpm.nodesource.com/setup_10.x | sudo bash -",
    "sudo yum -y install nodejs",
    "yum install --enablerepo=epel -y git",
    "pip install ansible",
    AnsiblePullCmd,
    "echo '*/10 * * * * root {}' > /etc/cron.d/ansible-pull".format(AnsiblePullCmd)
]))


t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-976152f2",
    InstanceType="t2.micro",
    SecurityGroups=[Ref("SecurityGroup")],
    KeyName=Ref("KeyPair"),
    UserData=ud,
    Tags=PoCTags,
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ]),
))

print (t.to_json())
