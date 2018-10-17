window.addEventListener('load', async () => {
    // Modern dapp browsers...
    if (window.ethereum) {
        window.web3 = new Web3(ethereum);
        try {
            // Request account access if needed
            await ethereum.enable();
            // Acccounts now exposed
            get_balances();
        } catch (error) {
            alert("Need MetaMask to use this dApp!");
        }
    }
    // Legacy dapp browsers...
    else if(window.web3) {
        window.web3 = new Web3(web3.currentProvider);
        // Acccounts always exposed
        get_balances();
    }
    // Non-dapp browsers...
    else {
        console.log('Non-Ethereum browser detected. You should consider trying MetaMask!');
    }
});

function get_balances(){
    window.web3.eth.getAccounts(function (err, accounts) {
        if(accounts[0]) {
            $.post( "/get_user_account", { user_account: accounts[0] });
            document.getElementById("user_account").innerHTML = accounts[0];
            document.getElementById("user_account").value = accounts[0];
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
        else document.getElementById("user_account").innerHTML = 'MetaMask is not enabled!';
        return null;
    });
}
