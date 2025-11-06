package k8srequireresourcelimits

# Test: Compliant deployment with all limits set
test_compliant_deployment {
  input := {
    "review": {
      "object": {
        "spec": {
          "template": {
            "spec": {
              "containers": [{
                "name": "nginx",
                "image": "nginx:latest",
                "resources": {
                  "limits": {
                    "cpu": "500m",
                    "memory": "512Mi"
                  }
                }
              }]
            }
          }
        }
      }
    },
    "parameters": {
      "exemptImages": []
    }
  }
  
  count(violation) == 0
}

# Test: Missing CPU limit
test_missing_cpu_limit {
  input := {
    "review": {
      "object": {
        "spec": {
          "template": {
            "spec": {
              "containers": [{
                "name": "nginx",
                "image": "nginx:latest",
                "resources": {
                  "limits": {
                    "memory": "512Mi"
                  }
                }
              }]
            }
          }
        }
      }
    },
    "parameters": {
      "exemptImages": []
    }
  }
  
  count(violation) > 0
}

# Test: Missing memory limit
test_missing_memory_limit {
  input := {
    "review": {
      "object": {
        "spec": {
          "template": {
            "spec": {
              "containers": [{
                "name": "nginx",
                "image": "nginx:latest",
                "resources": {
                  "limits": {
                    "cpu": "500m"
                  }
                }
              }]
            }
          }
        }
      }
    },
    "parameters": {
      "exemptImages": []
    }
  }
  
  count(violation) > 0
}

# Test: Exempt image should pass without limits
test_exempt_image {
  input := {
    "review": {
      "object": {
        "spec": {
          "template": {
            "spec": {
              "containers": [{
                "name": "proxy",
                "image": "k8s.gcr.io/kube-proxy:v1.28.0",
                "resources": {}
              }]
            }
          }
        }
      }
    },
    "parameters": {
      "exemptImages": ["k8s.gcr.io/kube-proxy"]
    }
  }
  
  count(violation) == 0
}
