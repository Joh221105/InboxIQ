import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RetailerLogo } from "@/components/packages/RetailerLogo";

describe("RetailerLogo", () => {
  it("resolves amazon.com sender domains to Amazon", () => {
    render(<RetailerLogo senderEmail="locker@amazon.com" />);

    expect(screen.getByLabelText("Amazon logo")).toBeInTheDocument();
  });

  it("resolves fedex.com sender domains to FedEx", () => {
    render(<RetailerLogo senderEmail="notify@fedex.com" />);

    expect(screen.getByLabelText("FedEx logo")).toBeInTheDocument();
  });

  it("falls back to package icon for unknown senders", () => {
    render(<RetailerLogo senderEmail="random@example.com" />);

    expect(screen.getByLabelText("Package")).toBeInTheDocument();
  });
});
