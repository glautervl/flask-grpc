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

const approveTokens = (user_account, agent) => {
    return new Promise((resolve, reject) => {
        agent.fundJob(
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
        let user_account = get_user_account();
        let agent = window.web3.eth.contract(agentAbi).at('0x333aCC524483853A4aDf4c9ccF4FE28801B5D43a');
        document.getElementById("fundJob").disabled = true;
        document.getElementById("fundJob").value = "Please, wait...";
        return approveTokens(user_account, agent);
    })
    .then((hash) => {
        return waitForReceipt(hash, function (receipt) {
            console.log(receipt);
            $.post( "/get_receipt", { receipt });
            document.getElementById("fundJob").value = "FundJob";
            document.getElementById("fundJob").disabled = false;
        });
    })
    .then((receipt) => {
        console.info('receipt', receipt);
    })
    .catch(console.error);