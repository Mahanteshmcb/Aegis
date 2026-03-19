require("@nomiclabs/hardhat-waffle");

module.exports = {
  solidity: "0.8.19",
  networks: {
    hardhat: {},
    // polygon: {
    //   url: process.env.POLYGON_RPC_URL,
    //   accounts: [process.env.PRIVATE_KEY]
    // }
  }
};