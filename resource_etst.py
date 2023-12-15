
num_subchannels = 1
num_subframes = 10
available_resources = set((sc, sf) for sc in range(num_subchannels) for sf in range(num_subframes))


def allocate(resources):
    if resources:
        resource = resources.pop()
        print(resource)
        return resource
    return (None, 0)

def release(resources, resource_id):
    release = resources.add(resource_id)
    print(release)


print(available_resources)
resource_id = allocate(available_resources)
print(available_resources)
release(available_resources, resource_id)
print(available_resources)

#print(available_resources)