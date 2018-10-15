window.user_account =  $(".consumer").text();
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
      error(err);
    }
    if (receipt !== null) {
      // Transaction went through
      if (cb) {
        cb(receipt);
      }
    } else {
      // Try again in 1 second
      window.setTimeout(function () {
        waitForReceipt(hash, cb);
      }, 1000);
    }
  });
}

const approveTokens = (contract) => {
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
        document.getElementById("fundJob").disabled = true;
        document.getElementById("fundJob").value = "Please, wait...";
        console.log("jobAddress: ", window.jobAddress);
        console.log("jobPrice: ", window.jobPrice);
        console.log("user_account: ", window.user_account);
        return approveTokens(window.token_contract);
    })
    .then((hash) => {
        console.log("hash: ", hash);
        return waitForReceipt(hash, function (receipt) {
            console.log(receipt);
            $.post( "/get_receipt", { receipt });
            return approveTokens(window.token_contract); // <<<======== HERE!
        });
    })
    .then((receipt) => {
        console.info('receipt', receipt);
    })
    .catch(console.error);