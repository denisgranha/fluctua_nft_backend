from eip712_structs import EIP712Struct, String, make_domain

domain_name = "Fluctua Records NFTs"
domain_version = 1
domain = make_domain(name=domain_name, version=domain_version)


class Person(EIP712Struct):
    email = String()

    def get_message(self):
        return self.to_message(domain)