
import { PropertySearch } from "@/components/PropertySearch";
import { PropertyTable } from "@/components/PropertyTable";
import { Property } from "@/types/property";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";

const mockProperties: Property[] = [
  {
    address: "6 Conisborough Crescent",
    price: 390000,
    bedrooms: 3,
    type: "Terraced House",
    timeOnMarket: "2 weeks",
    aiScore: 6,
  },
  {
    address: "24 Conisborough Crescent",
    price: 508000,
    bedrooms: 3,
    type: "Semi-detached",
    timeOnMarket: "1 month",
    aiScore: 8.1,
  },
  {
    address: "15 Oak Tree Lane",
    price: 675000,
    bedrooms: 4,
    type: "Detached",
    timeOnMarket: "3 weeks",
    aiScore: 7.5,
  },
  {
    address: "42 Garden View Road",
    price: 425000,
    bedrooms: 2,
    type: "Flat",
    timeOnMarket: "1 week",
    aiScore: 6.8,
  },
  {
    address: "78 Victoria Street",
    price: 950000,
    bedrooms: 5,
    type: "Victorian House",
    timeOnMarket: "2 months",
    aiScore: 9.2,
  },
  {
    address: "31 Riverside Court",
    price: 385000,
    bedrooms: 2,
    type: "Apartment",
    timeOnMarket: "5 days",
    aiScore: 7.1,
  },
  {
    address: "19 Cherry Blossom Avenue",
    price: 620000,
    bedrooms: 4,
    type: "Family Home",
    timeOnMarket: "6 weeks",
    aiScore: 8.4,
  }
];

const Index = () => {
  const { logout } = useAuth();
  const [properties] = useState<Property[]>(mockProperties);
  
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Property Finder</h1>
          <Button variant="outline" onClick={logout}>Logout</Button>
        </div>
        <PropertySearch />
        <PropertyTable properties={properties} showLimited={true} />
      </div>
    </div>
  );
};

export default Index;
