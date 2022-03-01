from eip712_structs import EIP712Struct, String, make_domain, Int

domain_name = "Fluctua Records NFTs"
domain_version = 1
domain = make_domain(name=domain_name, version=domain_version)


class Person(EIP712Struct):
    wallet = String()

    def get_message(self):
        return self.to_message(domain)


class NftContent(EIP712Struct):
    wallet = String()
    nft = Int()

    def get_message(self):
        return self.to_message(domain)
