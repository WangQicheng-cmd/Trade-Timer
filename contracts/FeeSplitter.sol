// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
}

contract FeeSplitter {
    // 运营方收款钱包地址（硬编码，部署后不可更改，0.2% 手续费自动转入此地址）
    address public constant FEE_WALLET = 0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6;
    address public immutable feeWallet;
    uint256 public constant FEE_PERCENT = 20;
    uint256 public constant FEE_DENOMINATOR = 10000;

    uint256 public totalFeesCollected;
    mapping(address => uint256) public tokenFeesCollected;

    event FeeCollected(
        address indexed token,
        address indexed user,
        uint256 feeAmount,
        uint256 timestamp
    );

    event FeesWithdrawn(
        address indexed token,
        address indexed to,
        uint256 amount,
        uint256 timestamp
    );

    constructor() {
        feeWallet = FEE_WALLET;
    }

    function splitFee(address token, uint256 totalAmount) external returns (uint256 feeAmount) {
        feeAmount = (totalAmount * FEE_PERCENT) / FEE_DENOMINATOR;

        require(
            IERC20(token).transferFrom(msg.sender, address(this), feeAmount),
            "FeeSplitter: fee transfer failed"
        );

        totalFeesCollected += feeAmount;
        tokenFeesCollected[token] += feeAmount;

        emit FeeCollected(token, msg.sender, feeAmount, block.timestamp);

        return feeAmount;
    }

    function splitFeeNative() external payable returns (uint256 feeAmount) {
        feeAmount = (msg.value * FEE_PERCENT) / FEE_DENOMINATOR;

        uint256 refundAmount = msg.value - feeAmount;
        if (refundAmount > 0) {
            (bool success, ) = payable(msg.sender).call{value: refundAmount}("");
            require(success, "FeeSplitter: refund failed");
        }

        totalFeesCollected += feeAmount;

        emit FeeCollected(address(0), msg.sender, feeAmount, block.timestamp);

        return feeAmount;
    }

    function withdrawFees(address token) external {
        uint256 balance;
        if (token == address(0)) {
            balance = address(this).balance;
            require(balance > 0, "FeeSplitter: no ETH fees to withdraw");
            (bool success, ) = payable(feeWallet).call{value: balance}("");
            require(success, "FeeSplitter: ETH transfer failed");
        } else {
            balance = IERC20(token).balanceOf(address(this));
            require(balance > 0, "FeeSplitter: no token fees to withdraw");
            require(
                IERC20(token).transfer(feeWallet, balance),
                "FeeSplitter: token transfer failed"
            );
        }

        emit FeesWithdrawn(token, feeWallet, balance, block.timestamp);
    }

    function getFeeAmount(uint256 totalAmount) external pure returns (uint256) {
        return (totalAmount * FEE_PERCENT) / FEE_DENOMINATOR;
    }

    function getUserAmountAfterFee(uint256 totalAmount) external pure returns (uint256) {
        return totalAmount - ((totalAmount * FEE_PERCENT) / FEE_DENOMINATOR);
    }

    receive() external payable {}
}
