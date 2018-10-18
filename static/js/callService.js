var Eth = window.Eth;
var md5 = window.md5;

window.jobAddress = $(".jobAddress").text();
window.jobPrice = $(".jobPrice").text();
window.job_contract = window.web3.eth.contract(jobAbi).at(window.jobAddress);
window.token_contract = window.web3.eth.contract(tokenAbi).at('0x3b226ff6aad7851d3263e53cb7688d13a07f6e81');
window.tokenAddress = "0x3b226ff6aad7851d3263e53cb7688d13a07f6e81";
window.receipt = null;
window.blockNumber = null;
window.transactionHash = "";
window.consumer = "";

function getLatestBlock() {
    window.web3.eth.getBlock('latest', function (err, res) {
        if (!err) {
            console.log('blockNumber["latest"]:', res.number);
            window.blockNumber = res.number;
        }
    });
}

const getCode = (contract) => {
    return new Promise((resolve, reject) => {
        contract.approve(
            window.jobAddress,
            parseInt(window.jobPrice),
            {from: window.user_account},
            (error, hash) => {
                if (!error) {
                    console.log('Transaction sent');
                    console.dir(hash);
                    resolve(hash);
                }
                else {
                    console.log(error);
                    reject(error);
                }
            }
        );
    });
};

function get_account(){
    window.web3.eth.getAccounts(function (err, accounts) {
        if(accounts[0]) {
            document.getElementById("user_account").innerHTML = accounts[0];
            document.getElementById("user_account").value = accounts[0];
            window.user_account = accounts[0];
            console.log("user_account[1]: ", window.user_account);
            window.web3.eth.getBalance(accounts[0], function (err, balance) {
                document.getElementById("eth_balance").innerHTML = window.web3.fromWei(balance, 'ether');
            });
            let tokenContract = window.web3.eth.contract(tokenAbi).at('0x3b226ff6aad7851d3263e53cb7688d13a07f6e81');
            tokenContract.balanceOf(accounts[0], (error, balance) => {
                tokenContract.decimals((error, decimals) => {
                  balance = balance.div(10**decimals);
                  document.getElementById("agi_balance").innerHTML = balance;
                });
            });
            return accounts[0];
        }
        else document.getElementById("user_account").innerHTML = 'MetaMask is not enabled!';
    });
}

get_account();
const isMainNetwork = () => {
    return new Promise((resolve, reject) => {
        window.web3.version.getNetwork((err, netId) => {
            if (err) {
                reject(err);
                return;
            }
            netId === '42' ? resolve() : reject('not kovan network');
            getLatestBlock();
        });
    });
};

isMainNetwork()
    .then(() => {
        document.getElementById("getResponse").disabled = true;
        document.getElementById("getResponse").textContent = "Please, wait...";

        console.log("jobAddress: ", window.jobAddress);
        console.log("jobPrice: ", window.jobPrice);
        window.job_state = -1;
        window.job_contract.state({from: window.user_account},
            function (error, jobState) {
                if (!error) {
                    window.jobState = jobState;
                    console.log("jobState: ", window.jobState);
                } else console.log("Error jobState: ", error);

            }
        );

        if(window.user_account) {
            if (window.user_account.includes("MetaMask")) {
                window.user_account = document.getElementById("user_account").value;
                console.log("user_account[2]: ", window.user_account);
            }
        }
        if (!window.user_account) document.getElementById("getResponse").textContent = "MetaMask is not enabled";
    })
    .then((state) => {
        console.log("jobState: ", state);
    })
    .then(() => {
        document.getElementById("getResponse").disabled = true;
        document.getElementById("getResponse").textContent = "Please, wait...";
        console.log("jobAddress: ", window.jobAddress);
        console.log("jobPrice: ", window.jobPrice);
        window.agent = window.web3.eth.contract(agentAbi).at(window.agent_address.value);

        const oldSigAgentBytecodeChecksum = "f4b0a8064a38abaf2630f5f6bd0043c8";
        let addressBytes = [];
        for(let i=2; i< window.jobAddress.length-1; i+=2) {
          addressBytes.push(parseInt(window.jobAddress.substr(i, 2), 16));
        }

        window.web3.eth.getCode(window.agent.address,
            function(error, bytecode) {
                if (!error) {
                    let bcBytes = [];
                    for (let i = 2; i < bytecode.length; i += 2) {
                        bcBytes.push(parseInt(bytecode.substr(i, 2), 16));
                    }
                    let bcSum = md5(bcBytes);
                    let sigPayload = bcSum === oldSigAgentBytecodeChecksum ? Eth.keccak256(addressBytes) : Eth.fromUtf8(window.jobAddress);

                    console.log("jobState: ", window.jobState);
                    console.log("user_account: ", window.user_account);
                    console.log("sigPayload: ", sigPayload);
                    //var eth_sign = new Eth(window.web3.currentProvider);
                    //eth_sign.personal_sign(sigPayload, window.user_account,
                    window.web3.personal.sign(sigPayload, window.user_account,
                        function (error, signature) {
                            if (!error) {
                                let r = `0x${signature.slice(2, 66)}`;
                                let s = `0x${signature.slice(66, 130)}`;
                                let v = parseInt(signature.slice(130, 132), 16);

                                window.agent.validateJobInvocation(window.jobAddress, v, r, s, {from: window.user_account},
                                    function (error, validateJob) {
                                        if (!error) {
                                            console.log('validateJobInvocation: ' + validateJob);
                                            // If agent is using old bytecode, put auth in params object. Otherwise, put auth in headers as new daemon
                                            // must be in use to support new signature scheme
                                            let callHeaders = bcSum === oldSigAgentBytecodeChecksum ? {} : {
                                                "snet-job-address": window.jobAddress,
                                                "snet-job-signature": signature
                                            };

                                            let addlParams = bcSum === oldSigAgentBytecodeChecksum ? {
                                                job_address: window.jobAddress,
                                                job_signature: signature
                                            } : {};

                                            console.log("callHeaders: ", callHeaders);
                                            console.log("addlParams: ", addlParams);
                                            console.log("SIGNATURE: ", signature);

                                            $.post("/get_signature", {
                                                job_address: window.jobAddress,
                                                job_signature: signature
                                            });

                                            document.getElementById("getResponse").disabled = false;
                                            if(validateJob) document.getElementById("getResponse").textContent = "GetResponse";
                                            else document.getElementById("getResponse").textContent = "JobFail";
                                        } else {
                                            document.getElementById("getResponse").textContent = "JobFail";
                                            console.log("Error validateJobInvocation: ", error);
                                        }
                                    });
                            } else console.log("Error personal_sign: ", error);
                        });
                } else console.log("Error getCode: ", error);
            });
    })
    .catch(console.error);