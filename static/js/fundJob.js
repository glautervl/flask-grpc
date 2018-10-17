window.user_account =  document.getElementById("user_address").textContent;
window.jobAddress = $(".jobAddress").text();
window.jobPrice = $(".jobPrice").text();
window.job_contract = window.web3.eth.contract(jobAbi).at(window.jobAddress);
window.token_contract = window.web3.eth.contract(tokenAbi).at('0x3b226ff6aad7851d3263e53cb7688d13a07f6e81');
window.tokenAddress = "0x3b226ff6aad7851d3263e53cb7688d13a07f6e81";
window.receipt = null;
window.blockNumber = 'latest';
window.transactionHash = "";
window.consumer = "";

function waitForReceipt(hash, cb) {
  window.web3.eth.getTransactionReceipt(hash, function (err, receipt) {
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
                waitForReceipt(hash, cb);
            }, 1000);
        }
    } else {
        window.setTimeout(function () {
            waitForReceipt(hash, cb);
        }, 1000);
    }

  });
}

function waitForEvent(contract, cb){
    if(window.blockNumber === null) window.blockNumber = 'latest';
    var event = contract.JobFunded({}, { fromBlock: window.blockNumber, toBlock: 'latest' }).get((err, eventResult) => {
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

const fundJob = (contract) => {
    return new Promise((resolve, reject) => {
        contract.fundJob(
            {from: window.user_account},
            (error, hash) => {
                if (!error) {
                    console.log('Funding Job...');
                    console.dir(hash);
                    window.hash = hash;
                    resolve(hash);
                }
                else {
                    console.log(error);
                    document.getElementById("callService").textContent = "Rejected";
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
            window.user_account =  document.getElementById("user_address").textContent;
        });
    });
};

isMainNetwork()
    .then(() => {
        document.getElementById("callService").disabled = true;
        document.getElementById("callService").textContent = "Please, wait...";
        console.log("jobAddress: ", window.jobAddress);
        console.log("jobPrice: ", window.jobPrice);
        console.log("user_account: ", window.user_account);
        if (window.user_account.includes("MetaMask")){
            document.getElementById("approveTokens").value = "MetaMask Disabled!";
            window.user_account =  document.getElementById("user_address").value;
            console.log("user_account: ", window.user_account);
        } else return fundJob(window.job_contract);
    })
    .then((hash) => {
        if(hash) window.hash = hash;
        console.log("hash:", window.hash);
        return waitForReceipt(hash, function (receipt) {
            console.log(receipt);
            console.log("blockNumber: ", receipt["blockNumber"]);
            console.log("transactionHash: ", receipt["transactionHash"]);
            window.blockNumber = receipt["blockNumber"];
            window.transactionHash = receipt["transactionHash"];
            $.post( "/get_receipt", { receipt });
        });
    })
    .then((receipt) => {
        console.log(receipt);
        return waitForEvent(window.job_contract, function (eventResult) {
            if(eventResult) {
                for(let i=0; i<eventResult.length; i++) {
                    var last_event = eventResult[i];
                    console.log("[fundJob] last_event:", last_event);
                    if (window.transactionHash === last_event["transactionHash"]) {
                        console.log("jobAddress: ", window.jobAddress);
                        document.getElementById("callService").textContent = "CallService";
                        document.getElementById("callService").disabled = false;
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
                console.log("[fundJob] No eventResult!");
                document.getElementById("callService").textContent = "JobFail!";
            }
        });
    })
    .catch(console.error);