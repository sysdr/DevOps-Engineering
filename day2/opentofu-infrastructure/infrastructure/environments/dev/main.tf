module "vpc" {
  source = "../../modules/vpc"
  
  environment        = "dev"
  vpc_cidr          = "10.0.0.0/16"
  availability_zones = ["us-west-2a", "us-west-2b"]
}

module "compute" {
  source = "../../modules/compute"
  
  environment       = "dev"
  vpc_id           = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  instance_type    = "t3.micro"
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "load_balancer_dns" {
  value = module.compute.load_balancer_dns
}
