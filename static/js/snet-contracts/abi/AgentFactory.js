const agentFactoryAbi = [
    {"constant":true,"inputs":[{"name":"","type":"uint256"}],"name":"createdAgents","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},
    {"constant":true,"inputs":[],"name":"token","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"_token","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},
    {"anonymous":false,"inputs":[{"indexed":false,"name":"agent","type":"address"}],"name":"AgentCreated","type":"event"},
    {"constant":false,"inputs":[{"name":"price","type":"uint256"},{"name":"endpoint","type":"string"},{"name":"metadataURI","type":"string"}],"name":"createAgent","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"function"}
    ];
