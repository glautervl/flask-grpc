window.user_account = get_user_account();
window.agent = window.web3.eth.contract(agentAbi).at('0x333aCC524483853A4aDf4c9ccF4FE28801B5D43a');
window.receipt = null;
window.blockNumber = 'latest';
window.transactionHash = "";
window.consumer = "";
window.jobAddress = "";
window.jobPrice = "";

function waitForReceipt(hash, cb) {
  window.web3.eth.getTransactionReceipt(hash, function (err, receipt) {
    if (err) {
      error(err);
    }
    if (receipt !== null) {
      // Transaction went through
      if (cb) {
        cb(receipt);
      }
    } else {
      // Try again in 1 second
      setTimeout(function () {
        waitForReceipt(hash, cb);
      }, 1000);
    }
  });
}

function waitForEvent(contract, cb){
    if(blockNumber === null) blockNumber = 'latest';
    var event = contract.JobCreated({}, { fromBlock: blockNumber, toBlock: 'latest' }).get((err, eventResult) => {
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

const createJob = (user_account, agent) => {
    return new Promise((resolve, reject) => {
        agent.createJob(
            {from: user_account},
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

const isMainNetwork = () => {
    return new Promise((resolve, reject) => {
        window.web3.version.getNetwork((err, netId) => {
            if (err) {
                reject(err);
                return;
            }
            netId === '42' ? resolve() : reject('not kovan network');
        });
    });
};

isMainNetwork()
    .then(() => {
        document.getElementById("approveTokens").disabled = true;
        document.getElementById("approveTokens").value = "Please, wait...";
        return createJob(user_account, agent);
    })
    .then((hash) => {
        console.log("hash:", hash);
        return waitForReceipt(hash, function (receipt) {
            console.log("blockNumber: ", receipt["blockNumber"]);
            console.log("transactionHash: ", receipt["transactionHash"]);
            window.blockNumber = receipt["blockNumber"];
            window.transactionHash = receipt["transactionHash"];
            $.post("/get_receipt", { receipt });
        });
    })
    .then((receipt) => {
        return waitForEvent(agent, function (eventResult) {
            console.log("eventResult:", eventResult);
            var last_event = eventResult[eventResult.length-1];
            if(last_event) {
                if(window.transactionHash === last_event["transactionHash"]) {
                    window.consumer = last_event["args"]["consumer"];
                    console.log("consumer: ", window.consumer);
                    window.jobAddress = last_event["args"]["job"];
                    console.log("jobAddress: ", window.jobAddress);
                    window.jobPrice = last_event["args"]["jobPrice"]["c"][0];
                    console.log("jobPrice: ", window.jobPrice);
                    document.getElementById("approveTokens").value = "ApproveTokens";
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
            else {
                document.getElementById("approveTokens").value = "JobFail!";
            }
        });
    })
    .then((eventResult) => {
        console.log("eventResult:", eventResult);
    })
    .catch(console.error);