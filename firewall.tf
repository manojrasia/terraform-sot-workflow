resource "google_compute_firewall" "rules" {
  for_each = var.firewall_rules
  project = each.value.project_id
  name = each.value.name
  network = each.value.network
  direction = each.value.direction
  priority = each.value.priority
  source_ranges = each.value.source_ranges
  target_tags = try(each.value.target_tags, [])
  dynamic "allow" {
    for_each = each.value.allowed
    content {
      protocol = allow.value.protocol
      ports = try(allow.value.ports, null)
    }
  }
}
