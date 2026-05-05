require("@nomiclabs/hardhat-waffle");
require("@nomiclabs/hardhat-ethers");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
      allowUnlimitedContractSize: true,
      loggingEnabled: true,
      // For private network simulation
      accounts: {
        mnemonic: "test test test test test test test test test test test junk",
        count: 10, // 10 accounts for testing multiple customers
      },
    },
    localhost: {
      url: "http://127.0.0.1:8545",
      accounts: process.env.PRIVATE_KEY && process.env.PRIVATE_KEY !== "" ? [process.env.PRIVATE_KEY] : [],
      chainId: 1337, // Standard localhost chainId
    },
    private: {
      url: "http://127.0.0.1:8545", // Can be changed to your private network URL
      accounts: process.env.PRIVATE_KEY && process.env.PRIVATE_KEY !== "" ? [process.env.PRIVATE_KEY] : [],
      chainId: 12345, // Custom chainId for private network
      gasPrice: 20000000000, // 20 gwei
    },
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    outputFile: "gas-report.txt",
    noColors: true,
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    artifacts: "./artifacts",
    cache: "./cache",
  },
  mocha: {
    timeout: 40000,
  },
};