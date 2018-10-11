
document.getElementById('wallet').innerHTML += 'Wallet: ';

if (typeof window.web3 !== 'undefined') {
    const ethereumProvider = web3.currentProvider;
    const myWeb3 = new Web3(ethereumProvider);
    web3.eth.getAccounts(function (err, accounts) {
        document.getElementById('wallet').innerHTML += accounts[0];
        web3.eth.getBalance(accounts[0], function (err, balance) {
            document.getElementById('wallet').innerHTML += '<br>ETH: ' + web3.fromWei(balance, 'ether');
        });
        let tokenContract = web3.eth.contract(tokenAbi).at('0x3b226ff6aad7851d3263e53cb7688d13a07f6e81');
        tokenContract.balanceOf(accounts[0], (error, balance) => {
            tokenContract.decimals((error, decimals) => {
              balance = balance.div(10**decimals);
              document.getElementById('wallet').innerHTML += '<br>AGI: ' + balance;
            });
        });

        let agent = web3.eth.contract(agentAbi).at('0x333aCC524483853A4aDf4c9ccF4FE28801B5D43a');
        listenForClicks(accounts[0], agent);
    });

} else {
    document.getElementById('wallet').innerHTML += 'MetaMask is not enabled!';
}




async function waitForTxToBeMined (txHash) {
  let txReceipt;
  while (!txReceipt) {
    try {
      txReceipt = await web3.eth.getTransactionReceipt(txHash)
    } catch (err) {
      return alert(err)
    }
  }
  alert("OK")
}

function listenForClicks (user_account, miniToken) {
  var button = document.querySelector('button.selectService');
  button.addEventListener('click', function(err, response) {
    miniToken.createJob({from: user_account},
        function (err, txHash) {
            if (!err) {
                console.log('Transaction sent');
                console.dir(txHash);
                waitForTxToBeMined(txHash)
            }
            else console.log(err);
        });
  });
}

