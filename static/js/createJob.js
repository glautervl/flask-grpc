window.receipt = null;
window.blockNumber = 'latest';
window.transactionHash = "";
window.consumer = "";
window.jobAddress = "";
window.jobPrice = "";
window.hash;

function waitForReceipt(cb) {
  window.web3.eth.getTransactionReceipt(window.hash, function (err, receipt) {
    if (err) {
      console.log(err);
    }
    if (receipt != null) {
        if(receipt["blockNumber"] !== null) {
            // Transaction went through
            if (cb) {
                cb(receipt);
            }
        } else {
            window.setTimeout(function () {
                waitForReceipt(cb);
            }, 1000);
        }
    } else {
        window.setTimeout(function () {
            waitForReceipt(cb);
        }, 1000);
    }

  });
}

function waitForEvent(contract, cb){
    if(window.blockNumber === null) window.blockNumber = 'latest';
    var event = contract.JobCreated({}, { fromBlock: window.blockNumber, toBlock: 'latest' }).get((err, eventResult) => {
        if (err) {
          console.log(err);
        }
        if (eventResult !== null && eventResult.length > 0)
        {
            if (cb) {
                cb(eventResult);
            }
        } else {
            setTimeout(function () {
                waitForEvent(contract, cb);
            }, 1000);
        }
    });
}

const createJob = (contract) => {
    return new Promise((resolve, reject) => {
        contract.createJob(
            {from: window.user_account},
            (error, hash) => {
                if (!error) {
                    console.log('Creating Job...');
                    console.dir(hash);
                    window.hash = hash;
                    resolve(hash);
                }
                else {
                    console.log(error);
                    document.getElementById("approveTokens").textContent = "Rejected";
                    reject(error);
                }
            }
        );
    });
};

function get_account(){
    window.web3.eth.getAccounts(function (err, accounts) {
        if(accounts[0]) {
            document.getElementById("user_address").innerHTML = accounts[0];
            document.getElementById("user_address").value = accounts[0];
            window.user_account = accounts[0];
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
        else document.getElementById("user_address").innerHTML = 'MetaMask is not enabled!';
    });
}

const isMainNetwork = () => {
    return new Promise((resolve, reject) => {
        window.web3.version.getNetwork((err, netId) => {
            if (err) {
                reject(err);
                return;
            }
            netId === '42' ? resolve() : reject('not kovan network');
            get_account();
            window.user_account =  document.getElementById("user_address").textContent;
        });
    });
};

isMainNetwork()
    .then(() => {
        document.getElementById("approveTokens").disabled = true;
        document.getElementById("approveTokens").textContent = "Please, wait...";
        window.agent_address =  document.getElementById("agent_address").value;
        console.log("agent_address: ", window.agent_address);
        window.agent = window.web3.eth.contract(agentAbi).at(window.agent_address);
        console.log("user_account: ", window.user_account);
        if (window.user_account.includes("MetaMask")){
            document.getElementById("approveTokens").value = "MetaMask Disabled!";
            window.user_account =  document.getElementById("user_address").value;
            console.log("user_account: ", window.user_account);
        } else return createJob(agent);
    })
    .then((hash) => {
        if(hash) window.hash = hash;
        console.log("hash:", window.hash);
        return waitForReceipt(function (receipt) {
            console.log("blockNumber: ", receipt["blockNumber"]);
            console.log("transactionHash: ", receipt["transactionHash"]);
            window.blockNumber = receipt["blockNumber"];
            window.transactionHash = receipt["transactionHash"];
            $.post("/get_receipt", { receipt });
        });
    })
    .then((receipt) => {
        return waitForEvent(agent, function (eventResult) {
            if(eventResult) {
                for(let i=0; i<eventResult.length; i++) {
                    var last_event = eventResult[i];
                    console.log("[createJob] last_event:", last_event);
                    if (window.transactionHash === last_event["transactionHash"]) {
                        window.consumer = last_event["args"]["consumer"];
                        console.log("consumer: ", window.consumer);
                        window.jobAddress = last_event["args"]["job"];
                        console.log("jobAddress: ", window.jobAddress);
                        window.jobPrice = last_event["args"]["jobPrice"]["c"][0];
                        console.log("jobPrice: ", window.jobPrice);
                        document.getElementById("approveTokens").textContent = "ApproveTokens";
                        document.getElementById("approveTokens").disabled = false;
                        $.post("/get_events", {
                            blockNumber: window.blockNumber,
                            transactionHash: window.transactionHash,
                            consumer: window.consumer,
                            jobAddress: window.jobAddress,
                            jobPrice: window.jobPrice
                        });
                    }
                }
            }
            else {
                console.log("[createJob] No eventResult!");
                document.getElementById("approveTokens").textContent = "JobFail!";
            }
        });
    })
    .catch(console.error);