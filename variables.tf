variable "project_apis" {
  type = map(list(string))
}
variable "project_roles" {
  type = map(any)
}
variable "service_account_roles" {
  type = list(any)
}
variable "shared_vpc_users" {
  type = list(any)
}
variable "firewall_rules" {
  type = map(any)
}
variable "gke_workload_identities" {
  type = list(any)
}
